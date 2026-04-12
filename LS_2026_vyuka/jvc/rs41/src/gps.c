#include "gps.h"

#include <stddef.h>

#include "board.h"
#include "platform.h"
#include "uart.h"

static gps_fix_t g_fix;
static char g_line[96];
static uint8_t g_line_len = 0;

static bool streq_prefix(const char *lhs, const char *rhs) {
    while (*rhs != '\0') {
        if (*lhs++ != *rhs++) {
            return false;
        }
    }
    return true;
}

static int hex_to_int(char c) {
    if (c >= '0' && c <= '9') {
        return c - '0';
    }
    if (c >= 'A' && c <= 'F') {
        return c - 'A' + 10;
    }
    if (c >= 'a' && c <= 'f') {
        return c - 'a' + 10;
    }
    return -1;
}

static bool parse_checksum(char *line) {
    uint8_t checksum = 0U;
    char *asterisk = NULL;

    if (*line != '$') {
        return false;
    }

    for (char *cursor = line + 1; *cursor != '\0'; ++cursor) {
        if (*cursor == '*') {
            asterisk = cursor;
            break;
        }
        checksum ^= (uint8_t) *cursor;
    }

    if (asterisk == NULL || (asterisk[1] == '\0') || (asterisk[2] == '\0')) {
        return false;
    }

    int hi = hex_to_int(asterisk[1]);
    int lo = hex_to_int(asterisk[2]);
    if (hi < 0 || lo < 0) {
        return false;
    }

    *asterisk = '\0';
    return checksum == (uint8_t) ((hi << 4) | lo);
}

static uint8_t split_fields(char *line, char **fields, uint8_t max_fields) {
    uint8_t count = 0U;
    char *cursor = line;

    while (cursor != NULL && count < max_fields) {
        fields[count++] = cursor;
        char *comma = cursor;
        while (*comma != '\0' && *comma != ',') {
            comma++;
        }
        if (*comma == '\0') {
            cursor = NULL;
        } else {
            *comma = '\0';
            cursor = comma + 1;
        }
    }

    return count;
}

static bool parse_u32(const char *text, uint32_t *value) {
    uint32_t result = 0U;
    if (*text == '\0') {
        return false;
    }

    while (*text != '\0') {
        if (*text < '0' || *text > '9') {
            return false;
        }
        result = result * 10U + (uint32_t) (*text - '0');
        text++;
    }

    *value = result;
    return true;
}

static bool parse_decimal_scaled(const char *text, uint32_t scale, int32_t *value) {
    bool negative = false;
    uint32_t whole = 0U;
    uint32_t frac = 0U;
    uint32_t frac_scale = 1U;

    if (*text == '-') {
        negative = true;
        text++;
    }

    if (*text == '\0') {
        return false;
    }

    while (*text != '\0' && *text != '.') {
        if (*text < '0' || *text > '9') {
            return false;
        }
        whole = whole * 10U + (uint32_t) (*text - '0');
        text++;
    }

    if (*text == '.') {
        text++;
        while (*text != '\0' && frac_scale < 1000000U) {
            if (*text < '0' || *text > '9') {
                return false;
            }
            frac = frac * 10U + (uint32_t) (*text - '0');
            frac_scale *= 10U;
            text++;
        }
    }

    int32_t scaled = (int32_t) (whole * scale);
    scaled += (int32_t) ((frac * scale) / frac_scale);
    *value = negative ? -scaled : scaled;
    return true;
}

static bool parse_latlon_e7(const char *text, bool longitude, char hemi, int32_t *out) {
    uint32_t whole = 0U;
    uint32_t frac = 0U;
    uint32_t frac_scale = 1U;
    uint32_t degrees;
    uint32_t minutes;
    uint32_t minute_scaled;
    int32_t value;

    if (*text == '\0') {
        return false;
    }

    while (*text != '\0' && *text != '.') {
        if (*text < '0' || *text > '9') {
            return false;
        }
        whole = whole * 10U + (uint32_t) (*text - '0');
        text++;
    }

    if (*text == '.') {
        text++;
        while (*text != '\0' && frac_scale < 10000000U) {
            if (*text < '0' || *text > '9') {
                return false;
            }
            frac = frac * 10U + (uint32_t) (*text - '0');
            frac_scale *= 10U;
            text++;
        }
    }

    degrees = whole / 100U;
    minutes = whole % 100U;
    minute_scaled = minutes * frac_scale + frac;

    value = (int32_t) (degrees * 10000000UL);
    value += (int32_t) ((minute_scaled * 10000000ULL) / (60ULL * frac_scale));

    if ((!longitude && hemi == 'S') || (longitude && hemi == 'W')) {
        value = -value;
    }

    *out = value;
    return true;
}

static void parse_gga(char **fields, uint8_t count) {
    uint32_t sats = 0U;
    int32_t altitude_cm = 0;
    int32_t lat = 0;
    int32_t lon = 0;

    if (count < 10U || fields[6][0] == '0') {
        g_fix.flags &= (uint8_t) ~(GPS_FLAG_POSITION_VALID | GPS_FLAG_ALTITUDE_VALID);
        return;
    }

    if (!parse_latlon_e7(fields[2], false, fields[3][0], &lat)) {
        return;
    }
    if (!parse_latlon_e7(fields[4], true, fields[5][0], &lon)) {
        return;
    }
    if (!parse_u32(fields[7], &sats)) {
        sats = 0U;
    }
    if (!parse_decimal_scaled(fields[9], 100, &altitude_cm)) {
        altitude_cm = 0;
    }

    g_fix.latitude_e7 = lat;
    g_fix.longitude_e7 = lon;
    g_fix.altitude_cm = altitude_cm;
    g_fix.satellites = (uint8_t) sats;
    g_fix.flags |= GPS_FLAG_POSITION_VALID | GPS_FLAG_ALTITUDE_VALID;
    g_fix.last_update_ms = platform_millis();
}

static void parse_rmc(char **fields, uint8_t count) {
    int32_t speed_milli_knots = 0;

    if (count < 8U || fields[2][0] != 'A') {
        g_fix.flags &= (uint8_t) ~GPS_FLAG_SPEED_VALID;
        return;
    }

    if (parse_decimal_scaled(fields[7], 1000U, &speed_milli_knots)) {
        uint32_t positive = (speed_milli_knots < 0) ? 0U : (uint32_t) speed_milli_knots;
        g_fix.speed_cms = (uint16_t) ((positive * 51444ULL) / 1000000ULL);
        g_fix.flags |= GPS_FLAG_SPEED_VALID;
        g_fix.last_update_ms = platform_millis();
    }
}

static void gps_process_line(char *line) {
    char *fields[16];
    uint8_t field_count;

    if (!parse_checksum(line)) {
        return;
    }

    field_count = split_fields(line + 1, fields, 16U);
    if (field_count == 0U) {
        return;
    }

    if (streq_prefix(fields[0], "GPGGA") || streq_prefix(fields[0], "GNGGA")) {
        parse_gga(fields, field_count);
    } else if (streq_prefix(fields[0], "GPRMC") || streq_prefix(fields[0], "GNRMC")) {
        parse_rmc(fields, field_count);
    }
}

void gps_init(void) {
    g_fix.latitude_e7 = 0;
    g_fix.longitude_e7 = 0;
    g_fix.altitude_cm = 0;
    g_fix.speed_cms = 0;
    g_fix.satellites = 0;
    g_fix.flags = 0;
    g_fix.last_update_ms = 0;
    g_line_len = 0;
}

void gps_poll(void) {
    uint8_t byte;

    while (uart1_read_byte(&byte)) {
        if (byte == '\r') {
            continue;
        }

        if (byte == '\n') {
            if (g_line_len > 0U) {
                g_line[g_line_len] = '\0';
                gps_process_line(g_line);
                g_line_len = 0U;
            }
            continue;
        }

        if (g_line_len >= (uint8_t) (sizeof(g_line) - 1U)) {
            g_line_len = 0U;
        }
        g_line[g_line_len++] = (char) byte;
    }

    if ((platform_millis() - g_fix.last_update_ms) > GPS_UART_TIMEOUT_MS) {
        g_fix.flags = 0;
        g_fix.satellites = 0;
        g_fix.speed_cms = 0;
    }
}

const gps_fix_t *gps_get_fix(void) {
    return &g_fix;
}
