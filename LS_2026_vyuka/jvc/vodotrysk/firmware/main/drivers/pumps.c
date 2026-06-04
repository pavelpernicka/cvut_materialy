#include "drivers/pumps.h"

#include <string.h>

#include "board/board_config.h"
#include "driver/gpio.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "system/config.h"
#include "system/logger.h"

static const char *TAG = "pumps";
static pump_state_t s_pumps[2];
static uint64_t s_fill_started_ms[2];
static uint64_t s_drain_cooldown_until_ms;
static uint64_t s_last_water_used_ms;

static pump_mode_t pump_mode_from_string(const char *mode)
{
    if (mode == NULL) return PUMP_MODE_OFF;
    if (strcmp(mode, "manual_on") == 0) return PUMP_MODE_MANUAL_ON;
    if (strcmp(mode, "two_level_sensors") == 0) return PUMP_MODE_TWO_LEVEL_SENSORS;
    if (strcmp(mode, "high_level_only") == 0) return PUMP_MODE_HIGH_LEVEL_ONLY;
    if (strcmp(mode, "timed_after_drain") == 0) return PUMP_MODE_TIMED_AFTER_DRAIN;
    if (strcmp(mode, "pwm_interval") == 0) return PUMP_MODE_PWM_INTERVAL;
    return PUMP_MODE_OFF;
}

static int pump_pin_for_index(uint8_t index)
{
    const board_config_t *board = board_config_get();
    return index == 0 ? board->pin_pump1 : board->pin_pump2;
}

static void set_reason(uint8_t index, const char *reason)
{
    strlcpy(s_pumps[index].last_reason, reason == NULL ? "" : reason, sizeof(s_pumps[index].last_reason));
}

static void pump_write(uint8_t index, bool on, const char *reason)
{
    const board_config_t *board = board_config_get();
    gpio_set_level(pump_pin_for_index(index), board->pump_outputs_inverted ? !on : on);
    if (s_pumps[index].output_on != on) {
        uint64_t now_ms = (uint64_t) (esp_timer_get_time() / 1000ULL);
        if (on) {
            s_pumps[index].last_switch_ms = now_ms;
            logger_event(LOG_CAT_PUMP, "pump%u on reason=%s", (unsigned) index + 1, reason == NULL ? "-" : reason);
        } else {
            if (s_pumps[index].last_switch_ms > 0 && now_ms > s_pumps[index].last_switch_ms) {
                s_pumps[index].last_runtime_ms = (uint32_t) (now_ms - s_pumps[index].last_switch_ms);
            }
            logger_event(LOG_CAT_PUMP, "pump%u off reason=%s runtime_ms=%u", (unsigned) index + 1, reason == NULL ? "-" : reason, (unsigned) s_pumps[index].last_runtime_ms);
        }
    }
    s_pumps[index].output_on = on;
    set_reason(index, reason);
}

static void apply_config_to_state(uint8_t index, const pump_config_model_t *cfg)
{
    s_pumps[index].enabled = cfg->enabled;
    s_pumps[index].mode = pump_mode_from_string(cfg->mode);
    s_pumps[index].max_current_a = cfg->max_current_a;
    s_pumps[index].min_current_when_on_a = cfg->min_current_when_on_a;
    s_pumps[index].fill_timeout_s = cfg->fill_timeout_s;
    s_pumps[index].interval_period_ms = cfg->interval_period_ms;
    s_pumps[index].duty_percent = cfg->duty_percent;
    s_pumps[index].only_after_water_used = cfg->only_after_water_used;
}

static const pump_config_model_t *config_for_index(uint8_t index)
{
    const app_config_t *cfg = config_get();
    return index == 0 ? &cfg->pumps.pump1 : &cfg->pumps.pump2;
}

static void pump_fault_shutdown(uint8_t index, const char *reason, bool overcurrent, bool undercurrent)
{
    s_pumps[index].fault_overcurrent = overcurrent;
    s_pumps[index].fault_undercurrent = undercurrent;
    s_pumps[index].auto_enabled = false;
    s_pumps[index].manual_override = false;
    s_pumps[index].mode = PUMP_MODE_OFF;
    pump_write(index, false, reason);
    logger_event(LOG_CAT_ERROR, "pump%u fault=%s current=%.3f", (unsigned) index + 1, reason, (double) s_pumps[index].current_a);
}

static void pumps_apply_fault_checks(uint8_t index)
{
    if (!s_pumps[index].output_on) {
        return;
    }
    if (s_pumps[index].current_a > s_pumps[index].max_current_a && s_pumps[index].max_current_a > 0.0f) {
        pump_fault_shutdown(index, "overcurrent", true, false);
        return;
    }
    if (s_pumps[index].current_a < s_pumps[index].min_current_when_on_a && s_pumps[index].min_current_when_on_a > 0.0f) {
        pump_fault_shutdown(index, "undercurrent", false, true);
    }
}

static void pumps_apply_auto_logic_for_index(uint8_t index, const sensor_snapshot_t *snapshot)
{
    if (!s_pumps[index].enabled || !s_pumps[index].auto_enabled || s_pumps[index].manual_override || snapshot == NULL) {
        return;
    }

    uint64_t now_ms = (uint64_t) (esp_timer_get_time() / 1000ULL);
    if (now_ms < s_drain_cooldown_until_ms) {
        pump_write(index, false, "drain_cooldown");
        return;
    }

    switch (s_pumps[index].mode) {
        case PUMP_MODE_TWO_LEVEL_SENSORS:
            if (snapshot->water_state == WATER_STATE_LOW) {
                if (!s_pumps[index].output_on) {
                    s_fill_started_ms[index] = now_ms;
                    s_pumps[index].timed_out = false;
                }
                pump_write(index, true, "level_low");
            } else if (snapshot->water_state == WATER_STATE_FILLING) {
                if (s_pumps[index].output_on && s_fill_started_ms[index] != 0 && s_pumps[index].fill_timeout_s > 0 &&
                    (now_ms - s_fill_started_ms[index]) > ((uint64_t) s_pumps[index].fill_timeout_s * 1000ULL)) {
                    s_pumps[index].timed_out = true;
                    pump_fault_shutdown(index, "fill_timeout", false, false);
                }
            } else if (snapshot->water_state == WATER_STATE_HIGH) {
                s_fill_started_ms[index] = 0;
                s_pumps[index].timed_out = false;
                pump_write(index, false, "level_high");
            } else if (snapshot->water_state == WATER_STATE_ERROR) {
                s_fill_started_ms[index] = 0;
                pump_write(index, false, "sensor_error");
            }
            break;

        case PUMP_MODE_HIGH_LEVEL_ONLY:
            if (snapshot->level_high) {
                pump_write(index, false, "high_level_only");
            } else if (!s_pumps[index].only_after_water_used || (now_ms - s_last_water_used_ms) < s_pumps[index].interval_period_ms) {
                pump_write(index, true, "high_level_refill");
            }
            break;

        case PUMP_MODE_TIMED_AFTER_DRAIN:
            if ((now_ms - s_last_water_used_ms) < s_pumps[index].interval_period_ms) {
                pump_write(index, true, "after_drain");
            } else {
                pump_write(index, false, "after_drain_idle");
            }
            break;

        case PUMP_MODE_PWM_INTERVAL: {
            if (s_pumps[index].interval_period_ms == 0) {
                pump_write(index, false, "interval_zero");
                break;
            }
            uint32_t on_ms = (uint32_t) (((uint64_t) s_pumps[index].interval_period_ms * s_pumps[index].duty_percent) / 100ULL);
            uint32_t phase = (uint32_t) (now_ms % s_pumps[index].interval_period_ms);
            bool should_on = phase < on_ms;
            if (s_pumps[index].only_after_water_used && (now_ms - s_last_water_used_ms) > s_pumps[index].interval_period_ms * 2ULL) {
                should_on = false;
            }
            pump_write(index, should_on, should_on ? "interval_on" : "interval_off");
            break;
        }

        default:
            break;
    }
}

esp_err_t pumps_init(void)
{
    const board_config_t *board = board_config_get();
    const gpio_config_t cfg = {
        .mode = GPIO_MODE_OUTPUT,
        .pin_bit_mask = (1ULL << board->pin_pump1) | (1ULL << board->pin_pump2),
    };
    ESP_RETURN_ON_ERROR(gpio_config(&cfg), TAG, "gpio config failed");

    memset(s_pumps, 0, sizeof(s_pumps));
    memset(s_fill_started_ms, 0, sizeof(s_fill_started_ms));
    ESP_RETURN_ON_ERROR(pumps_apply_config(0), TAG, "apply pump1 config failed");
    ESP_RETURN_ON_ERROR(pumps_apply_config(1), TAG, "apply pump2 config failed");
    s_pumps[0].auto_enabled = true;
    s_pumps[1].auto_enabled = false;
    pumps_all_off();
    ESP_LOGI(TAG, "Pump outputs initialized on GPIO%d/GPIO%d", board->pin_pump1, board->pin_pump2);
    return ESP_OK;
}

esp_err_t pumps_apply_config(uint8_t index)
{
    if (index > 1) {
        return ESP_ERR_INVALID_ARG;
    }
    apply_config_to_state(index, config_for_index(index));
    return ESP_OK;
}

esp_err_t pumps_set_config(uint8_t index, const pump_config_model_t *cfg)
{
    if (index > 1 || cfg == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    app_config_t next = *config_get();
    if (index == 0) {
        next.pumps.pump1 = *cfg;
    } else {
        next.pumps.pump2 = *cfg;
    }
    config_set(&next);
    return pumps_apply_config(index);
}

esp_err_t pumps_set_manual(uint8_t index, bool on)
{
    if (index > 1) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_pumps[index].enabled) {
        return ESP_ERR_INVALID_STATE;
    }
    s_pumps[index].manual_override = true;
    s_pumps[index].auto_enabled = false;
    s_pumps[index].timed_out = false;
    s_pumps[index].fault_overcurrent = false;
    s_pumps[index].fault_undercurrent = false;
    s_pumps[index].mode = on ? PUMP_MODE_MANUAL_ON : PUMP_MODE_OFF;
    pump_write(index, on, on ? "manual_on" : "manual_off");
    return ESP_OK;
}

esp_err_t pumps_set_auto(uint8_t index, bool enabled)
{
    if (index > 1) {
        return ESP_ERR_INVALID_ARG;
    }
    s_pumps[index].auto_enabled = enabled;
    s_pumps[index].manual_override = false;
    s_pumps[index].timed_out = false;
    s_pumps[index].fault_overcurrent = false;
    s_pumps[index].fault_undercurrent = false;
    if (!enabled) {
        s_pumps[index].mode = PUMP_MODE_OFF;
        pump_write(index, false, "auto_off");
    } else {
        apply_config_to_state(index, config_for_index(index));
        set_reason(index, "auto_enabled");
    }
    return ESP_OK;
}

esp_err_t pumps_update_from_levels(const sensor_snapshot_t *snapshot)
{
    if (snapshot == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (snapshot->water_state == WATER_STATE_FILLING || snapshot->water_state == WATER_STATE_HIGH) {
        s_last_water_used_ms = (uint64_t) (esp_timer_get_time() / 1000ULL);
    }
    for (uint8_t i = 0; i < 2; ++i) {
        pumps_apply_auto_logic_for_index(i, snapshot);
        pumps_apply_fault_checks(i);
    }
    return ESP_OK;
}

void pumps_start_drain_cooldown(uint32_t cooldown_ms)
{
    s_last_water_used_ms = (uint64_t) (esp_timer_get_time() / 1000ULL);
    s_drain_cooldown_until_ms = s_last_water_used_ms + cooldown_ms;
    pump_write(0, false, "drain_cooldown");
}

esp_err_t pumps_get_state(uint8_t index, pump_state_t *out_state)
{
    if (index > 1 || out_state == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    *out_state = s_pumps[index];
    return ESP_OK;
}

esp_err_t pumps_set_current(uint8_t index, float current_a)
{
    if (index > 1) {
        return ESP_ERR_INVALID_ARG;
    }
    s_pumps[index].current_a = current_a;
    if (current_a > s_pumps[index].max_current_a) {
        s_pumps[index].max_current_a = current_a;
    }
    return ESP_OK;
}

void pumps_all_off(void)
{
    memset(s_fill_started_ms, 0, sizeof(s_fill_started_ms));
    pump_write(0, false, "all_off");
    pump_write(1, false, "all_off");
}
