#include "protocol.h"

#include <stdbool.h>
#include <stddef.h>

enum {
    AX25_FLAG = 0x7E,
    AX25_CONTROL_UI = 0x03,
    AX25_PID_NO_LAYER3 = 0xF0,
};

static uint16_t crc16_x25(const uint8_t *data, size_t length) {
    uint16_t crc = 0xFFFFU;

    for (size_t i = 0; i < length; ++i) {
        crc ^= data[i];
        for (uint8_t bit = 0; bit < 8U; ++bit) {
            if ((crc & 0x0001U) != 0U) {
                crc = (uint16_t) ((crc >> 1U) ^ 0x8408U);
            } else {
                crc >>= 1U;
            }
        }
    }

    return (uint16_t) ~crc;
}

static void append_char(char *buffer, size_t *pos, char ch) {
    if (*pos < AX25_MAX_INFO_BYTES) {
        buffer[*pos] = ch;
    }
    *pos += 1U;
}

static void append_text(char *buffer, size_t *pos, const char *text) {
    while (*text != '\0') {
        append_char(buffer, pos, *text++);
    }
}

static void append_uint_padded(char *buffer, size_t *pos, uint32_t value, uint8_t width) {
    char digits[10];

    for (uint8_t i = 0U; i < width; ++i) {
        digits[width - 1U - i] = (char) ('0' + (value % 10U));
        value /= 10U;
    }

    for (uint8_t i = 0U; i < width; ++i) {
        append_char(buffer, pos, digits[i]);
    }
}

static void append_signed_two_digits(char *buffer, size_t *pos, int16_t value) {
    if (value < 0) {
        append_char(buffer, pos, '-');
        append_uint_padded(buffer, pos, (uint32_t) (-value), 2U);
    } else {
        append_char(buffer, pos, '+');
        append_uint_padded(buffer, pos, (uint32_t) value, 2U);
    }
}

static void encode_address_field(uint8_t *dest, const char *callsign, uint8_t ssid, bool last) {
    uint8_t index = 0U;

    while (callsign[index] != '\0' && index < 6U) {
        dest[index] = (uint8_t) (callsign[index] << 1U);
        index++;
    }

    while (index < 6U) {
        dest[index++] = (uint8_t) (' ' << 1U);
    }

    dest[6] = (uint8_t) (0x60U | ((ssid & 0x0FU) << 1U) | (last ? 0x01U : 0x00U));
}

static void format_aprs_coordinate(char *dest, uint8_t degree_width, int32_t value_e7, char positive_hemisphere, char negative_hemisphere) {
    uint32_t absolute_value = (value_e7 < 0) ? (uint32_t) (-(int64_t) value_e7) : (uint32_t) value_e7;
    uint32_t degrees = absolute_value / 10000000U;
    uint32_t fraction = absolute_value % 10000000U;
    uint32_t minutes_x100 = (uint32_t) (((uint64_t) fraction * 6000U + 5000000U) / 10000000U);
    uint32_t minutes_whole;
    uint32_t minutes_frac;
    size_t pos = 0U;

    if (minutes_x100 >= 6000U) {
        degrees += 1U;
        minutes_x100 -= 6000U;
    }

    minutes_whole = minutes_x100 / 100U;
    minutes_frac = minutes_x100 % 100U;

    append_uint_padded(dest, &pos, degrees, degree_width);
    append_uint_padded(dest, &pos, minutes_whole, 2U);
    append_char(dest, &pos, '.');
    append_uint_padded(dest, &pos, minutes_frac, 2U);
    append_char(dest, &pos, (value_e7 < 0) ? negative_hemisphere : positive_hemisphere);
}

static uint32_t altitude_feet_from_cm(int32_t altitude_cm) {
    if (altitude_cm <= 0) {
        return 0U;
    }

    return (uint32_t) (((int64_t) altitude_cm * 125U + 1905U) / 3810U);
}

static uint16_t speed_knots_from_cms(uint16_t speed_cms) {
    return (uint16_t) (((uint32_t) speed_cms * 3600U + 92600U) / 185200U);
}

static size_t build_position_info(char *info, const gps_fix_t *fix, uint16_t battery_mv, int16_t mcu_temp_centi) {
    char latitude[8];
    char longitude[9];
    size_t pos = 0U;
    uint32_t altitude_ft = altitude_feet_from_cm(fix->altitude_cm);
    uint16_t speed_knots = speed_knots_from_cms(fix->speed_cms);
    int16_t temp_c = (int16_t) (mcu_temp_centi / 100);

    if (altitude_ft > 999999U) {
        altitude_ft = 999999U;
    }
    if (speed_knots > 999U) {
        speed_knots = 999U;
    }
    if (temp_c > 99) {
        temp_c = 99;
    } else if (temp_c < -99) {
        temp_c = -99;
    }

    format_aprs_coordinate(latitude, 2U, fix->latitude_e7, 'N', 'S');
    format_aprs_coordinate(longitude, 3U, fix->longitude_e7, 'E', 'W');

    append_char(info, &pos, '!');
    for (size_t i = 0U; i < sizeof(latitude); ++i) {
        append_char(info, &pos, latitude[i]);
    }
    append_char(info, &pos, '/');
    for (size_t i = 0U; i < sizeof(longitude); ++i) {
        append_char(info, &pos, longitude[i]);
    }
    append_char(info, &pos, 'O');
    append_text(info, &pos, "000/");
    append_uint_padded(info, &pos, speed_knots, 3U);
    append_text(info, &pos, "/A=");
    append_uint_padded(info, &pos, altitude_ft, 6U);
    append_char(info, &pos, 'V');
    append_uint_padded(info, &pos, battery_mv, 4U);
    append_char(info, &pos, 'T');
    append_signed_two_digits(info, &pos, temp_c);

    return (pos <= AX25_MAX_INFO_BYTES) ? pos : AX25_MAX_INFO_BYTES;
}

static size_t build_status_info(char *info, uint32_t uptime_ms, const gps_fix_t *fix, uint16_t battery_mv, int16_t mcu_temp_centi) {
    size_t pos = 0U;
    uint32_t uptime_s = uptime_ms / 1000U;
    int16_t temp_c = (int16_t) (mcu_temp_centi / 100);

    if (temp_c > 99) {
        temp_c = 99;
    } else if (temp_c < -99) {
        temp_c = -99;
    }

    append_text(info, &pos, ">NOFIX ");
    append_char(info, &pos, 'V');
    append_uint_padded(info, &pos, battery_mv, 4U);
    append_text(info, &pos, " T");
    append_signed_two_digits(info, &pos, temp_c);
    append_text(info, &pos, " U");
    append_uint_padded(info, &pos, uptime_s % 100000000U, 8U);
    append_text(info, &pos, " Q");
    append_uint_padded(info, &pos, fix->satellites, 2U);

    return (pos <= AX25_MAX_INFO_BYTES) ? pos : AX25_MAX_INFO_BYTES;
}

size_t protocol_build_packet(uint8_t *packet,
                             uint32_t uptime_ms,
                             const gps_fix_t *fix,
                             uint16_t battery_mv,
                             int16_t mcu_temp_centi) {
    char info[AX25_MAX_INFO_BYTES];
    size_t info_length;
    size_t frame_pos = 0U;
    uint16_t fcs;

    for (size_t i = 0U; i < AX25_MAX_FRAME_BYTES; ++i) {
        packet[i] = 0U;
    }

    packet[frame_pos++] = AX25_FLAG;
    encode_address_field(packet + frame_pos, AX25_DEST_CALLSIGN, AX25_DEST_SSID, false);
    frame_pos += 7U;
    encode_address_field(packet + frame_pos, AX25_SOURCE_CALLSIGN, AX25_SOURCE_SSID, true);
    frame_pos += 7U;
    packet[frame_pos++] = AX25_CONTROL_UI;
    packet[frame_pos++] = AX25_PID_NO_LAYER3;

    if ((fix->flags & GPS_FLAG_POSITION_VALID) != 0U) {
        info_length = build_position_info(info, fix, battery_mv, mcu_temp_centi);
    } else {
        info_length = build_status_info(info, uptime_ms, fix, battery_mv, mcu_temp_centi);
    }

    for (size_t i = 0U; i < info_length; ++i) {
        packet[frame_pos++] = (uint8_t) info[i];
    }

    fcs = crc16_x25(packet + 1U, frame_pos - 1U);
    packet[frame_pos++] = (uint8_t) (fcs & 0xFFU);
    packet[frame_pos++] = (uint8_t) (fcs >> 8U);
    packet[frame_pos++] = AX25_FLAG;

    return frame_pos;
}
