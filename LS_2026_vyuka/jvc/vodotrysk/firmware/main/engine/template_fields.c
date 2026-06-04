#include "engine/template_fields.h"

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "drivers/pumps.h"
#include "drivers/sensors.h"
#include "engine/queue.h"
#include "engine/water_engine.h"
#include "esp_check.h"
#include "esp_timer.h"
#include "system/diagnostics.h"
#include "system/wifi_manager.h"

static esp_err_t append_text(char *output, size_t output_size, size_t *cursor, const char *text)
{
    int written = snprintf(output + *cursor, output_size - *cursor, "%s", text);
    if (written < 0 || (size_t) written >= output_size - *cursor) {
        return ESP_ERR_NO_MEM;
    }
    *cursor += (size_t) written;
    return ESP_OK;
}

static const char *water_state_name(water_level_state_t state)
{
    switch (state) {
        case WATER_STATE_LOW: return "LOW";
        case WATER_STATE_FILLING: return "FILLING";
        case WATER_STATE_HIGH: return "HIGH";
        case WATER_STATE_ERROR: return "ERROR";
        default: return "UNKNOWN";
    }
}

static const char *pump_state_name(const pump_state_t *pump)
{
    if (pump == NULL) {
        return "--";
    }
    if (pump->manual_override) {
        return pump->output_on ? "MANUAL_ON" : "MANUAL_OFF";
    }
    if (pump->auto_enabled) {
        return pump->output_on ? "AUTO_ON" : "AUTO_OFF";
    }
    return pump->output_on ? "ON" : "OFF";
}

static void format_float(char *out, size_t out_size, float value, int decimals)
{
    if (decimals < 0 || decimals > 4) {
        decimals = 1;
    }
    snprintf(out, out_size, "%.*f", decimals, (double) value);
}

static bool template_value_for_key(const char *key, int decimals, char *out, size_t out_size)
{
    time_t now = time(NULL);
    struct tm tm_now;
    localtime_r(&now, &tm_now);
    const sensor_snapshot_t *sensors = sensors_get_cached();
    water_engine_status_t engine = water_engine_get_status();
    wifi_status_t wifi = wifi_manager_get_status();
    diagnostics_snapshot_t diag = {0};
    pump_state_t pump1 = {0};
    pump_state_t pump2 = {0};
    (void) diagnostics_get_snapshot(&diag);
    (void) pumps_get_state(0, &pump1);
    (void) pumps_get_state(1, &pump2);

    if (strcmp(key, "time") == 0) {
        strftime(out, out_size, "%H:%M", &tm_now);
    } else if (strcmp(key, "time_sec") == 0) {
        strftime(out, out_size, "%H:%M:%S", &tm_now);
    } else if (strcmp(key, "hour") == 0) {
        strftime(out, out_size, "%H", &tm_now);
    } else if (strcmp(key, "minute") == 0) {
        strftime(out, out_size, "%M", &tm_now);
    } else if (strcmp(key, "second") == 0) {
        strftime(out, out_size, "%S", &tm_now);
    } else if (strcmp(key, "date") == 0) {
        strftime(out, out_size, "%F", &tm_now);
    } else if (strcmp(key, "day") == 0) {
        strftime(out, out_size, "%d", &tm_now);
    } else if (strcmp(key, "month") == 0) {
        strftime(out, out_size, "%m", &tm_now);
    } else if (strcmp(key, "year") == 0) {
        strftime(out, out_size, "%Y", &tm_now);
    } else if (strcmp(key, "weekday") == 0) {
        strftime(out, out_size, "%a", &tm_now);
    } else if (strcmp(key, "temp") == 0) {
        format_float(out, out_size, sensors->temperature_c, decimals);
    } else if (strcmp(key, "humidity") == 0) {
        format_float(out, out_size, sensors->humidity_pct, decimals);
    } else if (strcmp(key, "pump1_state") == 0) {
        snprintf(out, out_size, "%s", pump_state_name(&pump1));
    } else if (strcmp(key, "pump2_state") == 0) {
        snprintf(out, out_size, "%s", pump_state_name(&pump2));
    } else if (strcmp(key, "pump1_current") == 0) {
        format_float(out, out_size, pump1.current_a, decimals);
    } else if (strcmp(key, "pump2_current") == 0) {
        format_float(out, out_size, pump2.current_a, decimals);
    } else if (strcmp(key, "pump1_current_max") == 0) {
        format_float(out, out_size, pump1.max_current_a, decimals);
    } else if (strcmp(key, "pump2_current_max") == 0) {
        format_float(out, out_size, pump2.max_current_a, decimals);
    } else if (strcmp(key, "level_low") == 0) {
        snprintf(out, out_size, "%s", sensors->level_low ? "1" : "0");
    } else if (strcmp(key, "level_high") == 0) {
        snprintf(out, out_size, "%s", sensors->level_high ? "1" : "0");
    } else if (strcmp(key, "water_state") == 0) {
        snprintf(out, out_size, "%s", water_state_name(sensors->water_state));
    } else if (strcmp(key, "queue_len") == 0) {
        snprintf(out, out_size, "%u", (unsigned) queue_len());
    } else if (strcmp(key, "ip") == 0) {
        snprintf(out, out_size, "%s", wifi.ip[0] != '\0' ? wifi.ip : "--");
    } else if (strcmp(key, "ssid") == 0) {
        snprintf(out, out_size, "%s", wifi.ssid[0] != '\0' ? wifi.ssid : "--");
    } else if (strcmp(key, "uptime") == 0) {
        snprintf(out, out_size, "%" PRIu64, diag.uptime_ms / 1000ULL);
    } else if (strcmp(key, "mode") == 0) {
        snprintf(out, out_size, "%s", wifi.mode);
    } else if (strcmp(key, "free_heap") == 0) {
        snprintf(out, out_size, "%u", (unsigned) diag.free_heap_bytes);
    } else if (strcmp(key, "fps") == 0) {
        snprintf(out, out_size, "%u", (unsigned) engine.fps);
    } else {
        return false;
    }
    return true;
}

esp_err_t template_fields_render(const char *input, char *output, size_t output_size)
{
    if (input == NULL || output == NULL || output_size == 0) {
        return ESP_ERR_INVALID_ARG;
    }

    const char *cursor = input;
    size_t out = 0;
    output[0] = '\0';

    while (*cursor != '\0') {
        const char *start = strstr(cursor, "{{");
        if (start == NULL) {
            ESP_RETURN_ON_ERROR(append_text(output, output_size, &out, cursor), "tpl", "append tail failed");
            break;
        }
        if (start > cursor) {
            char chunk[128];
            size_t len = (size_t) (start - cursor);
            if (len >= sizeof(chunk)) {
                len = sizeof(chunk) - 1;
            }
            memcpy(chunk, cursor, len);
            chunk[len] = '\0';
            ESP_RETURN_ON_ERROR(append_text(output, output_size, &out, chunk), "tpl", "append prefix failed");
        }
        const char *end = strstr(start, "}}");
        if (end == NULL) {
            ESP_RETURN_ON_ERROR(append_text(output, output_size, &out, start), "tpl", "append unterminated failed");
            break;
        }

        char key[48];
        size_t len = (size_t) (end - (start + 2));
        if (len >= sizeof(key)) {
            len = sizeof(key) - 1;
        }
        memcpy(key, start + 2, len);
        key[len] = '\0';

        int decimals = 1;
        char *fmt = strchr(key, ':');
        if (fmt != NULL) {
            *fmt++ = '\0';
            decimals = atoi(fmt);
        }

        char value[64];
        if (!template_value_for_key(key, decimals, value, sizeof(value))) {
            snprintf(value, sizeof(value), "--");
        }
        ESP_RETURN_ON_ERROR(append_text(output, output_size, &out, value), "tpl", "append value failed");
        cursor = end + 2;
    }

    return ESP_OK;
}
