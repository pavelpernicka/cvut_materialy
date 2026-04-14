#include "protocol.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "crc16.h"

enum {
    TELEMETRY_MAGIC_0 = 'R',
    TELEMETRY_MAGIC_1 = 'S',
    TELEMETRY_HEADER_BYTES = 12U,
    TELEMETRY_CRC_OFFSET = TELEMETRY_PACKET_BYTES - 2U,
    TLV_BOARD_STATUS = 0x01U,
    TLV_GPS_POSITION = 0x02U,
    TLV_GPS_MOTION = 0x03U,
    FLAG_GPS_POSITION_VALID = 1U << 0,
    FLAG_GPS_ALTITUDE_VALID = 1U << 1,
    FLAG_GPS_SPEED_VALID = 1U << 2,
};

static uint16_t g_sequence;

static uint8_t whiten_byte(uint16_t *lfsr) {
    uint8_t mask = 0U;

    for (uint8_t bit = 0U; bit < 8U; ++bit) {
        uint16_t feedback = (uint16_t) (((*lfsr >> 0U) ^ (*lfsr >> 5U)) & 0x01U);
        mask |= (uint8_t) (((*lfsr & 0x01U) != 0U ? 1U : 0U) << bit);
        *lfsr = (uint16_t) ((*lfsr >> 1U) | (feedback << 8U));
    }

    return mask;
}

static void whiten_packet(uint8_t *packet) {
    uint16_t lfsr = 0x01FFU;

    for (size_t i = 2U; i < TELEMETRY_PACKET_BYTES; ++i) {
        packet[i] ^= whiten_byte(&lfsr);
    }
}

static void write_u16_le(uint8_t *dest, uint16_t value) {
    dest[0] = (uint8_t) (value & 0xFFU);
    dest[1] = (uint8_t) (value >> 8U);
}

static void write_s16_le(uint8_t *dest, int16_t value) {
    write_u16_le(dest, (uint16_t) value);
}

static void write_u32_le(uint8_t *dest, uint32_t value) {
    dest[0] = (uint8_t) (value & 0xFFU);
    dest[1] = (uint8_t) ((value >> 8U) & 0xFFU);
    dest[2] = (uint8_t) ((value >> 16U) & 0xFFU);
    dest[3] = (uint8_t) ((value >> 24U) & 0xFFU);
}

static void write_s32_le(uint8_t *dest, int32_t value) {
    write_u32_le(dest, (uint32_t) value);
}

static bool append_tlv_header(uint8_t *packet, size_t *payload_pos, uint8_t type, uint8_t length) {
    if ((*payload_pos + 2U + length) > TELEMETRY_CRC_OFFSET) {
        return false;
    }

    packet[(*payload_pos)++] = type;
    packet[(*payload_pos)++] = length;
    return true;
}

static void append_board_status(uint8_t *packet, size_t *payload_pos, uint16_t battery_mv, int16_t mcu_temp_centi) {
    if (!append_tlv_header(packet, payload_pos, TLV_BOARD_STATUS, 4U)) {
        return;
    }

    write_u16_le(packet + *payload_pos, battery_mv);
    *payload_pos += 2U;
    write_s16_le(packet + *payload_pos, mcu_temp_centi);
    *payload_pos += 2U;
}

static void append_gps_position(uint8_t *packet, size_t *payload_pos, const gps_fix_t *fix) {
    if (!append_tlv_header(packet, payload_pos, TLV_GPS_POSITION, 12U)) {
        return;
    }

    write_s32_le(packet + *payload_pos, fix->latitude_e7);
    *payload_pos += 4U;
    write_s32_le(packet + *payload_pos, fix->longitude_e7);
    *payload_pos += 4U;
    write_s32_le(packet + *payload_pos, fix->altitude_cm);
    *payload_pos += 4U;
}

static void append_gps_motion(uint8_t *packet, size_t *payload_pos, const gps_fix_t *fix) {
    uint16_t speed_cms = ((fix->flags & GPS_FLAG_SPEED_VALID) != 0U) ? fix->speed_cms : 0U;

    if (!append_tlv_header(packet, payload_pos, TLV_GPS_MOTION, 3U)) {
        return;
    }

    write_u16_le(packet + *payload_pos, speed_cms);
    *payload_pos += 2U;
    packet[(*payload_pos)++] = fix->satellites;
}

size_t protocol_build_packet(uint8_t *packet,
                             uint32_t uptime_ms,
                             const gps_fix_t *fix,
                             uint16_t battery_mv,
                             int16_t mcu_temp_centi) {
    uint8_t flags = 0U;
    size_t payload_pos = TELEMETRY_HEADER_BYTES;
    uint16_t crc;

    for (size_t i = 0U; i < TELEMETRY_PACKET_BYTES; ++i) {
        packet[i] = 0U;
    }

    if ((fix->flags & GPS_FLAG_POSITION_VALID) != 0U) {
        flags |= FLAG_GPS_POSITION_VALID;
    }
    if ((fix->flags & GPS_FLAG_ALTITUDE_VALID) != 0U) {
        flags |= FLAG_GPS_ALTITUDE_VALID;
    }
    if ((fix->flags & GPS_FLAG_SPEED_VALID) != 0U) {
        flags |= FLAG_GPS_SPEED_VALID;
    }

    packet[0] = TELEMETRY_MAGIC_0;
    packet[1] = TELEMETRY_MAGIC_1;
    packet[2] = TELEMETRY_PROTOCOL_VERSION;
    packet[3] = flags;
    write_u16_le(packet + 4U, g_sequence++);
    write_u32_le(packet + 6U, uptime_ms);

    append_board_status(packet, &payload_pos, battery_mv, mcu_temp_centi);
    append_gps_motion(packet, &payload_pos, fix);

    if ((fix->flags & GPS_FLAG_POSITION_VALID) != 0U) {
        append_gps_position(packet, &payload_pos, fix);
    }

    packet[10] = (uint8_t) (payload_pos - TELEMETRY_HEADER_BYTES);
    packet[11] = 0U;

    crc = crc16_ccitt_false(packet, TELEMETRY_CRC_OFFSET);
    write_u16_le(packet + TELEMETRY_CRC_OFFSET, crc);
    whiten_packet(packet);

    return TELEMETRY_PACKET_BYTES;
}
