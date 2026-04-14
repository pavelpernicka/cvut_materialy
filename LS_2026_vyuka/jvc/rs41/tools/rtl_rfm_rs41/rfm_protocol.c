#include "rtl_rfm.h"
#include "rfm_protocol.h"

#define AMBLEMASK 0x0000FFFFUL
#define AMBLE 0x00002DD4UL
#define PACKET_LEN 48
#define PROTOCOL_VERSION_V1 1
#define PROTOCOL_VERSION_V2 2
#define FLAG_GPS_POSITION_VALID (1U << 0)
#define FLAG_GPS_ALTITUDE_VALID (1U << 1)
#define FLAG_GPS_SPEED_VALID (1U << 2)
#define TLV_BOARD_STATUS 0x01U
#define TLV_GPS_POSITION 0x02U
#define TLV_GPS_MOTION 0x03U

static CB_VOID open_cb;
static CB_VOID close_cb;

static uint8_t packet_buffer[PACKET_LEN];
static uint8_t packet_bi = 0;
static int bitphase = -1;
static uint8_t thisbyte = 0;
static uint32_t amble = 0;

static uint16_t crc16_ccitt_false(const uint8_t *data, size_t length)
{
    uint16_t crc = 0xFFFFU;

    for (size_t i = 0; i < length; ++i)
    {
        crc ^= (uint16_t) data[i] << 8;
        for (int bit = 0; bit < 8; ++bit)
        {
            crc = (crc & 0x8000U) ? (uint16_t) ((crc << 1) ^ 0x1021U) : (uint16_t) (crc << 1);
        }
    }

    return crc;
}

static uint8_t whiten_byte(uint16_t *lfsr)
{
    uint8_t mask = 0U;

    for (int bit = 0; bit < 8; ++bit)
    {
        uint16_t feedback = (uint16_t) (((*lfsr >> 0U) ^ (*lfsr >> 5U)) & 0x01U);
        mask |= (uint8_t) (((*lfsr & 0x01U) != 0U ? 1U : 0U) << bit);
        *lfsr = (uint16_t) ((*lfsr >> 1U) | (feedback << 8U));
    }

    return mask;
}

static void dewhiten_packet(uint8_t *data, size_t length)
{
    uint16_t lfsr = 0x01FFU;

    for (size_t i = 2U; i < length; ++i)
    {
        data[i] ^= whiten_byte(&lfsr);
    }
}

static uint16_t read_u16_le(const uint8_t *data)
{
    return (uint16_t) data[0] | ((uint16_t) data[1] << 8U);
}

static int16_t read_s16_le(const uint8_t *data)
{
    return (int16_t) read_u16_le(data);
}

static uint32_t read_u32_le(const uint8_t *data)
{
    return ((uint32_t) data[0]) |
           ((uint32_t) data[1] << 8U) |
           ((uint32_t) data[2] << 16U) |
           ((uint32_t) data[3] << 24U);
}

static int32_t read_s32_le(const uint8_t *data)
{
    return (int32_t) read_u32_le(data);
}

static int appendf(char *buffer, size_t size, int offset, const char *format, ...)
{
    va_list args;
    int written;

    if ((size_t) offset >= size)
    {
        return offset;
    }

    va_start(args, format);
    written = vsnprintf(buffer + offset, size - (size_t) offset, format, args);
    va_end(args);

    if (written < 0)
    {
        return offset;
    }

    if ((size_t) written >= size - (size_t) offset)
    {
        return (int) size;
    }

    return offset + written;
}

static void print_hex_frame(const uint8_t *data, size_t length)
{
    printv("FRAME=");
    for (size_t i = 0; i < length; ++i)
    {
        printv("%02X", data[i]);
    }
    printv("\n");
}

static int validate_packet(uint8_t *decoded)
{
    uint8_t version;
    uint16_t crc_rx;
    uint16_t crc_calc;

    if (decoded[0] != 'R' || decoded[1] != 'S')
    {
        return 0;
    }

    version = decoded[2];
    if (version != PROTOCOL_VERSION_V1 && version != PROTOCOL_VERSION_V2)
    {
        return 0;
    }

    crc_rx = read_u16_le(decoded + PACKET_LEN - 2U);
    crc_calc = crc16_ccitt_false(decoded, PACKET_LEN - 2U);
    if (crc_rx != crc_calc)
    {
        return 0;
    }

    return 1;
}

static char *format_packet_string(const uint8_t *raw)
{
    uint8_t decoded[PACKET_LEN];
    uint8_t flags;
    uint8_t payload_len;
    uint16_t sequence;
    uint32_t uptime_ms;
    int offset = 0;
    size_t pos = 12U;
    uint16_t battery_mv = 0U;
    int16_t mcu_temp_centi = 0;
    uint16_t speed_cms = 0U;
    uint8_t satellites = 0U;
    int32_t latitude_e7 = 0;
    int32_t longitude_e7 = 0;
    int32_t altitude_cm = 0;
    bool have_board = false;
    bool have_motion = false;
    bool have_position = false;
    char *result;

    memcpy(decoded, raw, PACKET_LEN);
    print_hex_frame(raw, PACKET_LEN);

    if (!validate_packet(decoded))
    {
        dewhiten_packet(decoded, PACKET_LEN);
    }

    if (!validate_packet(decoded))
    {
        uint16_t crc_rx = read_u16_le(decoded + PACKET_LEN - 2U);
        uint16_t crc_calc = crc16_ccitt_false(decoded, PACKET_LEN - 2U);
        printv("CRC mismatch: rx=%04X calc=%04X\n", crc_rx, crc_calc);
        print_hex_frame(decoded, PACKET_LEN);
        return NULL;
    }

    flags = decoded[3];
    sequence = read_u16_le(decoded + 4U);
    uptime_ms = read_u32_le(decoded + 6U);
    payload_len = decoded[10];

    if ((size_t) payload_len > (PACKET_LEN - 14U))
    {
        printv("Invalid payload length: %u\n", payload_len);
        return NULL;
    }

    while ((pos + 2U) <= (size_t) (12U + payload_len))
    {
        uint8_t tlv_type = decoded[pos++];
        uint8_t tlv_len = decoded[pos++];

        if ((pos + tlv_len) > (size_t) (12U + payload_len))
        {
            printv("TLV overflow\n");
            return NULL;
        }

        if (tlv_type == TLV_BOARD_STATUS && tlv_len == 4U)
        {
            battery_mv = read_u16_le(decoded + pos);
            mcu_temp_centi = read_s16_le(decoded + pos + 2U);
            have_board = true;
        }
        else if (tlv_type == TLV_GPS_MOTION && tlv_len == 3U)
        {
            speed_cms = read_u16_le(decoded + pos);
            satellites = decoded[pos + 2U];
            have_motion = true;
        }
        else if (tlv_type == TLV_GPS_POSITION && tlv_len == 12U)
        {
            latitude_e7 = read_s32_le(decoded + pos);
            longitude_e7 = read_s32_le(decoded + pos + 4U);
            altitude_cm = read_s32_le(decoded + pos + 8U);
            have_position = true;
        }

        pos += tlv_len;
    }

    result = malloc(256U);
    if (result == NULL)
    {
        return NULL;
    }

    offset = appendf(result, 256U, offset, "seq=%u uptime=%lums gps=%u",
                     sequence,
                     (unsigned long) uptime_ms,
                     (flags & FLAG_GPS_POSITION_VALID) ? 1U : 0U);

    if (have_motion)
    {
        offset = appendf(result, 256U, offset, " sats=%u", satellites);
    }
    if ((flags & FLAG_GPS_POSITION_VALID) && have_position)
    {
        offset = appendf(result, 256U, offset, " lat=%.7f lon=%.7f",
                         latitude_e7 / 1e7,
                         longitude_e7 / 1e7);
    }
    if ((flags & FLAG_GPS_ALTITUDE_VALID) && have_position)
    {
        offset = appendf(result, 256U, offset, " alt=%.2fm", altitude_cm / 100.0);
    }
    if ((flags & FLAG_GPS_SPEED_VALID) && have_motion)
    {
        offset = appendf(result, 256U, offset, " speed=%.2fm/s", speed_cms / 100.0);
    }
    if (have_board)
    {
        offset = appendf(result, 256U, offset, " batt=%umV temp=%.2fC",
                         battery_mv,
                         mcu_temp_centi / 100.0);
    }

    return result;
}

void rfm_init(CB_VOID o, CB_VOID c)
{
    open_cb = o;
    close_cb = c;
}

static char *process_byte(uint8_t thebyte)
{
    packet_buffer[packet_bi++] = thebyte;

    if (packet_bi < PACKET_LEN)
    {
        return NULL;
    }

    bitphase = -1;
    close_cb();
    return format_packet_string(packet_buffer);
}

char *rfm_decode(uint8_t thebit)
{
    if (thebit > 1U)
    {
        return NULL;
    }

    if (bitphase < 0)
    {
        amble = (amble << 1U) | (uint32_t) (thebit & 0x01U);

        if ((amble & AMBLEMASK) == AMBLE)
        {
            open_cb();
            packet_bi = 0U;
            bitphase = 0;
            thisbyte = 0U;
        }
    }
    else
    {
        thisbyte = (uint8_t) ((thisbyte << 1U) | (thebit & 0x01U));
        bitphase++;

        if (bitphase > 7)
        {
            bitphase = 0;
            return process_byte(thisbyte);
        }
    }

    return NULL;
}

void rfm_reset(void)
{
    bitphase = -1;
    thisbyte = 0U;
    amble = 0U;
    packet_bi = 0U;
}
