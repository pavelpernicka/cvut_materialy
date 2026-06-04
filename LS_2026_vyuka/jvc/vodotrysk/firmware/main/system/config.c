#include "system/config.h"

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static app_config_t s_config;

void config_load_defaults(app_config_t *out_config)
{
    app_config_t cfg = {
        .version = 1,
        .device_name = "Water Curtain",
        .wifi = {
            .mode = "ap_client",
            .ap_ssid = "WaterCurtain",
            .ap_password = "waterwater",
            .fallback_ap = true,
        },
        .hardware = {
            .solenoid_count = 64,
            .shift_register_count = 8,
            .bit_order_msb_first = true,
            .invert_outputs = false,
        },
        .engine = {
            .column_period_ms = 35,
            .default_frame_duration_ms = 35,
            .pre_flush_ms = 100,
            .post_flush_ms = 100,
            .max_active_valves = 64,
        },
        .exhibition = {
            .enabled = true,
            .max_queue = 50,
            .max_text_length = 32,
            .allow_bitmap = true,
            .cooldown_s = 5,
        },
        .pumps = {
            .pump1 = {
                .enabled = true,
                .mode = "two_level_sensors",
                .invert_output = false,
                .max_current_a = 5.0f,
                .min_current_when_on_a = 0.1f,
                .fill_timeout_s = 60,
                .interval_period_ms = 10000,
                .duty_percent = 40,
                .only_after_water_used = true,
            },
            .pump2 = {
                .enabled = true,
                .mode = "off",
                .invert_output = false,
                .max_current_a = 5.0f,
                .min_current_when_on_a = 0.1f,
                .fill_timeout_s = 60,
                .interval_period_ms = 10000,
                .duty_percent = 40,
                .only_after_water_used = false,
            },
        },
        .sensors = {
            .level_low_invert = false,
            .level_high_invert = false,
            .level_debounce_ms = 100,
            .pump1_fill_timeout_s = 60,
            .current_adc_scale = 1.0f,
            .current_adc_offset = 0.0f,
        },
    };

    for (uint8_t i = 0; i < 64; ++i) {
        cfg.hardware.valve_map[i] = i;
    }

    if (out_config != NULL) {
        *out_config = cfg;
    }
}

const app_config_t *config_get(void)
{
    return &s_config;
}

void config_set(const app_config_t *config)
{
    if (config != NULL) {
        s_config = *config;
    }
}

static bool json_find_key(const char *json, const char *key, const char **out_value)
{
    char needle[64];
    snprintf(needle, sizeof(needle), "\"%s\":", key);
    const char *p = strstr(json, needle);
    if (p == NULL) {
        return false;
    }
    *out_value = p + strlen(needle);
    return true;
}

static bool json_parse_string(const char *json, const char *key, char *dst, size_t dst_size)
{
    char needle[64];
    snprintf(needle, sizeof(needle), "\"%s\":\"", key);
    const char *p = strstr(json, needle);
    if (p == NULL) {
        return false;
    }
    p += strlen(needle);
    size_t i = 0;
    while (p[i] != '\0' && p[i] != '"' && i + 1 < dst_size) {
        dst[i] = p[i];
        ++i;
    }
    dst[i] = '\0';
    return true;
}

static bool json_parse_bool(const char *json, const char *key, bool *dst)
{
    const char *p = NULL;
    if (!json_find_key(json, key, &p)) {
        return false;
    }
    while (*p == ' ' || *p == '\t') {
        ++p;
    }
    if (strncmp(p, "true", 4) == 0) {
        *dst = true;
        return true;
    }
    if (strncmp(p, "false", 5) == 0) {
        *dst = false;
        return true;
    }
    return false;
}

static bool json_parse_u32(const char *json, const char *key, uint32_t *dst)
{
    const char *p = NULL;
    if (!json_find_key(json, key, &p)) {
        return false;
    }
    *dst = (uint32_t) strtoul(p, NULL, 10);
    return true;
}

static bool json_parse_float(const char *json, const char *key, float *dst)
{
    const char *p = NULL;
    if (!json_find_key(json, key, &p)) {
        return false;
    }
    *dst = strtof(p, NULL);
    return true;
}

static const char *json_find_section(const char *json, const char *key)
{
    char needle[64];
    snprintf(needle, sizeof(needle), "\"%s\":{", key);
    const char *p = strstr(json, needle);
    return p == NULL ? NULL : p + strlen(needle);
}

esp_err_t config_to_json(const app_config_t *config, char **out_json)
{
    if (config == NULL || out_json == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    char valve_map[256];
    int cursor = 0;
    for (size_t i = 0; i < 64; ++i) {
        cursor += snprintf(valve_map + cursor,
            sizeof(valve_map) - (size_t) cursor,
            "%s%u",
            i == 0 ? "" : ",",
            config->hardware.valve_map[i]);
    }

    size_t capacity = 2300;
    char *printed = calloc(capacity, 1);
    if (printed == NULL) {
        return ESP_ERR_NO_MEM;
    }

    snprintf(printed,
        capacity,
        "{"
        "\"version\":%" PRIu32 ","
        "\"device_name\":\"%s\","
        "\"wifi\":{\"mode\":\"%s\",\"ap_ssid\":\"%s\",\"ap_password\":\"%s\",\"client_ssid\":\"%s\",\"client_password\":\"%s\",\"fallback_ap\":%s},"
        "\"hardware\":{\"solenoid_count\":%u,\"shift_register_count\":%u,\"bit_order_msb_first\":%s,\"invert_outputs\":%s,\"valve_map\":[%s]},"
        "\"engine\":{\"column_period_ms\":%" PRIu32 ",\"default_frame_duration_ms\":%" PRIu32 ",\"pre_flush_ms\":%" PRIu32 ",\"post_flush_ms\":%" PRIu32 ",\"max_active_valves\":%u},"
        "\"exhibition\":{\"enabled\":%s,\"max_queue\":%u,\"max_text_length\":%u,\"allow_bitmap\":%s,\"cooldown_s\":%u},"
        "\"pumps\":{\"pump1\":{\"enabled\":%s,\"mode\":\"%s\",\"invert_output\":%s,\"max_current_a\":%.3f,\"min_current_when_on_a\":%.3f,\"fill_timeout_s\":%" PRIu32 ",\"interval_period_ms\":%" PRIu32 ",\"duty_percent\":%u,\"only_after_water_used\":%s},"
        "\"pump2\":{\"enabled\":%s,\"mode\":\"%s\",\"invert_output\":%s,\"max_current_a\":%.3f,\"min_current_when_on_a\":%.3f,\"fill_timeout_s\":%" PRIu32 ",\"interval_period_ms\":%" PRIu32 ",\"duty_percent\":%u,\"only_after_water_used\":%s}},"
        "\"sensors\":{\"level_low_invert\":%s,\"level_high_invert\":%s,\"level_debounce_ms\":%" PRIu32 ",\"pump1_fill_timeout_s\":%" PRIu32 ",\"current_adc_scale\":%.5f,\"current_adc_offset\":%.5f}"
        "}",
        config->version,
        config->device_name,
        config->wifi.mode,
        config->wifi.ap_ssid,
        config->wifi.ap_password,
        config->wifi.client_ssid,
        config->wifi.client_password,
        config->wifi.fallback_ap ? "true" : "false",
        config->hardware.solenoid_count,
        config->hardware.shift_register_count,
        config->hardware.bit_order_msb_first ? "true" : "false",
        config->hardware.invert_outputs ? "true" : "false",
        valve_map,
        config->engine.column_period_ms,
        config->engine.default_frame_duration_ms,
        config->engine.pre_flush_ms,
        config->engine.post_flush_ms,
        config->engine.max_active_valves,
        config->exhibition.enabled ? "true" : "false",
        config->exhibition.max_queue,
        config->exhibition.max_text_length,
        config->exhibition.allow_bitmap ? "true" : "false",
        config->exhibition.cooldown_s,
        config->pumps.pump1.enabled ? "true" : "false",
        config->pumps.pump1.mode,
        config->pumps.pump1.invert_output ? "true" : "false",
        (double) config->pumps.pump1.max_current_a,
        (double) config->pumps.pump1.min_current_when_on_a,
        config->pumps.pump1.fill_timeout_s,
        config->pumps.pump1.interval_period_ms,
        config->pumps.pump1.duty_percent,
        config->pumps.pump1.only_after_water_used ? "true" : "false",
        config->pumps.pump2.enabled ? "true" : "false",
        config->pumps.pump2.mode,
        config->pumps.pump2.invert_output ? "true" : "false",
        (double) config->pumps.pump2.max_current_a,
        (double) config->pumps.pump2.min_current_when_on_a,
        config->pumps.pump2.fill_timeout_s,
        config->pumps.pump2.interval_period_ms,
        config->pumps.pump2.duty_percent,
        config->pumps.pump2.only_after_water_used ? "true" : "false",
        config->sensors.level_low_invert ? "true" : "false",
        config->sensors.level_high_invert ? "true" : "false",
        config->sensors.level_debounce_ms,
        config->sensors.pump1_fill_timeout_s,
        (double) config->sensors.current_adc_scale,
        (double) config->sensors.current_adc_offset);

    *out_json = printed;
    return ESP_OK;
}

esp_err_t config_from_json(const char *json, app_config_t *out_config)
{
    if (json == NULL || out_config == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    app_config_t cfg;
    config_load_defaults(&cfg);

    json_parse_u32(json, "version", &cfg.version);
    json_parse_string(json, "device_name", cfg.device_name, sizeof(cfg.device_name));
    json_parse_string(json, "mode", cfg.wifi.mode, sizeof(cfg.wifi.mode));
    json_parse_string(json, "ap_ssid", cfg.wifi.ap_ssid, sizeof(cfg.wifi.ap_ssid));
    json_parse_string(json, "ap_password", cfg.wifi.ap_password, sizeof(cfg.wifi.ap_password));
    json_parse_string(json, "client_ssid", cfg.wifi.client_ssid, sizeof(cfg.wifi.client_ssid));
    json_parse_string(json, "client_password", cfg.wifi.client_password, sizeof(cfg.wifi.client_password));
    json_parse_bool(json, "fallback_ap", &cfg.wifi.fallback_ap);

    uint32_t tmp_u32 = 0;
    bool tmp_bool = false;
    if (json_parse_u32(json, "solenoid_count", &tmp_u32)) cfg.hardware.solenoid_count = (uint8_t) tmp_u32;
    if (json_parse_u32(json, "shift_register_count", &tmp_u32)) cfg.hardware.shift_register_count = (uint8_t) tmp_u32;
    if (json_parse_bool(json, "bit_order_msb_first", &tmp_bool)) cfg.hardware.bit_order_msb_first = tmp_bool;
    if (json_parse_bool(json, "invert_outputs", &tmp_bool)) cfg.hardware.invert_outputs = tmp_bool;
    json_parse_u32(json, "column_period_ms", &cfg.engine.column_period_ms);
    json_parse_u32(json, "default_frame_duration_ms", &cfg.engine.default_frame_duration_ms);
    json_parse_u32(json, "pre_flush_ms", &cfg.engine.pre_flush_ms);
    json_parse_u32(json, "post_flush_ms", &cfg.engine.post_flush_ms);
    if (json_parse_u32(json, "max_active_valves", &tmp_u32)) cfg.engine.max_active_valves = (uint8_t) tmp_u32;
    if (json_parse_bool(json, "enabled", &tmp_bool)) cfg.exhibition.enabled = tmp_bool;
    if (json_parse_u32(json, "max_queue", &tmp_u32)) cfg.exhibition.max_queue = (uint8_t) tmp_u32;
    if (json_parse_u32(json, "max_text_length", &tmp_u32)) cfg.exhibition.max_text_length = (uint8_t) tmp_u32;
    if (json_parse_bool(json, "allow_bitmap", &tmp_bool)) cfg.exhibition.allow_bitmap = tmp_bool;
    if (json_parse_u32(json, "cooldown_s", &tmp_u32)) cfg.exhibition.cooldown_s = (uint8_t) tmp_u32;

    const char *pump1 = json_find_section(json, "pump1");
    if (pump1 != NULL) {
        if (json_parse_bool(pump1, "enabled", &tmp_bool)) cfg.pumps.pump1.enabled = tmp_bool;
        json_parse_string(pump1, "mode", cfg.pumps.pump1.mode, sizeof(cfg.pumps.pump1.mode));
        if (json_parse_bool(pump1, "invert_output", &tmp_bool)) cfg.pumps.pump1.invert_output = tmp_bool;
        json_parse_float(pump1, "max_current_a", &cfg.pumps.pump1.max_current_a);
        json_parse_float(pump1, "min_current_when_on_a", &cfg.pumps.pump1.min_current_when_on_a);
        json_parse_u32(pump1, "fill_timeout_s", &cfg.pumps.pump1.fill_timeout_s);
        if (json_parse_u32(pump1, "interval_period_ms", &tmp_u32)) cfg.pumps.pump1.interval_period_ms = tmp_u32;
        if (json_parse_u32(pump1, "duty_percent", &tmp_u32)) cfg.pumps.pump1.duty_percent = (uint8_t) tmp_u32;
        if (json_parse_bool(pump1, "only_after_water_used", &tmp_bool)) cfg.pumps.pump1.only_after_water_used = tmp_bool;
    }
    const char *pump2 = json_find_section(json, "pump2");
    if (pump2 != NULL) {
        if (json_parse_bool(pump2, "enabled", &tmp_bool)) cfg.pumps.pump2.enabled = tmp_bool;
        json_parse_string(pump2, "mode", cfg.pumps.pump2.mode, sizeof(cfg.pumps.pump2.mode));
        if (json_parse_bool(pump2, "invert_output", &tmp_bool)) cfg.pumps.pump2.invert_output = tmp_bool;
        json_parse_float(pump2, "max_current_a", &cfg.pumps.pump2.max_current_a);
        json_parse_float(pump2, "min_current_when_on_a", &cfg.pumps.pump2.min_current_when_on_a);
        json_parse_u32(pump2, "fill_timeout_s", &cfg.pumps.pump2.fill_timeout_s);
        if (json_parse_u32(pump2, "interval_period_ms", &tmp_u32)) cfg.pumps.pump2.interval_period_ms = tmp_u32;
        if (json_parse_u32(pump2, "duty_percent", &tmp_u32)) cfg.pumps.pump2.duty_percent = (uint8_t) tmp_u32;
        if (json_parse_bool(pump2, "only_after_water_used", &tmp_bool)) cfg.pumps.pump2.only_after_water_used = tmp_bool;
    }

    if (json_parse_bool(json, "level_low_invert", &tmp_bool)) cfg.sensors.level_low_invert = tmp_bool;
    if (json_parse_bool(json, "level_high_invert", &tmp_bool)) cfg.sensors.level_high_invert = tmp_bool;
    json_parse_u32(json, "level_debounce_ms", &cfg.sensors.level_debounce_ms);
    json_parse_u32(json, "pump1_fill_timeout_s", &cfg.sensors.pump1_fill_timeout_s);
    json_parse_float(json, "current_adc_scale", &cfg.sensors.current_adc_scale);
    json_parse_float(json, "current_adc_offset", &cfg.sensors.current_adc_offset);

    const char *valve_map = strstr(json, "\"valve_map\":[");
    if (valve_map != NULL) {
        valve_map += strlen("\"valve_map\":[");
        for (size_t i = 0; i < 64; ++i) {
            cfg.hardware.valve_map[i] = (uint8_t) strtoul(valve_map, (char **) &valve_map, 10);
            while (*valve_map == ' ' || *valve_map == ',') {
                ++valve_map;
            }
            if (*valve_map == ']') {
                break;
            }
        }
    }

    *out_config = cfg;
    return ESP_OK;
}
