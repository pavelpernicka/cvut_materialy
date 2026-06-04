#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"
#include "drivers/sensors.h"
#include "system/config.h"

typedef enum {
    PUMP_MODE_OFF = 0,
    PUMP_MODE_MANUAL_ON,
    PUMP_MODE_TWO_LEVEL_SENSORS,
    PUMP_MODE_HIGH_LEVEL_ONLY,
    PUMP_MODE_TIMED_AFTER_DRAIN,
    PUMP_MODE_PWM_INTERVAL,
} pump_mode_t;

typedef struct {
    bool enabled;
    pump_mode_t mode;
    bool output_on;
    bool manual_override;
    bool auto_enabled;
    bool timed_out;
    float current_a;
    float max_current_a;
    float min_current_when_on_a;
    uint32_t fill_timeout_s;
    uint32_t interval_period_ms;
    uint8_t duty_percent;
    bool only_after_water_used;
    bool fault_overcurrent;
    bool fault_undercurrent;
    uint64_t last_switch_ms;
    uint32_t last_runtime_ms;
    char last_reason[24];
} pump_state_t;

esp_err_t pumps_init(void);
esp_err_t pumps_set_manual(uint8_t index, bool on);
esp_err_t pumps_set_auto(uint8_t index, bool enabled);
esp_err_t pumps_apply_config(uint8_t index);
esp_err_t pumps_set_config(uint8_t index, const pump_config_model_t *cfg);
esp_err_t pumps_update_from_levels(const sensor_snapshot_t *snapshot);
void pumps_start_drain_cooldown(uint32_t cooldown_ms);
esp_err_t pumps_get_state(uint8_t index, pump_state_t *out_state);
esp_err_t pumps_set_current(uint8_t index, float current_a);
void pumps_all_off(void);
