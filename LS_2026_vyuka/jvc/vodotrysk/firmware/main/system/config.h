#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"

typedef struct {
    char mode[16];
    char ap_ssid[32];
    char ap_password[32];
    char client_ssid[32];
    char client_password[64];
    bool fallback_ap;
} wifi_config_model_t;

typedef struct {
    uint8_t solenoid_count;
    uint8_t shift_register_count;
    bool bit_order_msb_first;
    bool invert_outputs;
    uint8_t valve_map[64];
} hardware_config_t;

typedef struct {
    uint32_t column_period_ms;
    uint32_t default_frame_duration_ms;
    uint32_t pre_flush_ms;
    uint32_t post_flush_ms;
    uint8_t max_active_valves;
} engine_config_t;

typedef struct {
    bool enabled;
    uint8_t max_queue;
    uint8_t max_text_length;
    bool allow_bitmap;
    uint8_t cooldown_s;
} exhibition_config_t;

typedef struct {
    bool level_low_invert;
    bool level_high_invert;
    uint32_t level_debounce_ms;
    uint32_t pump1_fill_timeout_s;
    float current_adc_scale;
    float current_adc_offset;
} sensor_config_t;

typedef struct {
    bool enabled;
    char mode[24];
    bool invert_output;
    float max_current_a;
    float min_current_when_on_a;
    uint32_t fill_timeout_s;
    uint32_t interval_period_ms;
    uint8_t duty_percent;
    bool only_after_water_used;
} pump_config_model_t;

typedef struct {
    uint32_t version;
    char device_name[32];
    wifi_config_model_t wifi;
    hardware_config_t hardware;
    engine_config_t engine;
    exhibition_config_t exhibition;
    struct {
        pump_config_model_t pump1;
        pump_config_model_t pump2;
    } pumps;
    sensor_config_t sensors;
} app_config_t;

void config_load_defaults(app_config_t *out_config);
const app_config_t *config_get(void);
void config_set(const app_config_t *config);
esp_err_t config_to_json(const app_config_t *config, char **out_json);
esp_err_t config_from_json(const char *json, app_config_t *out_config);
