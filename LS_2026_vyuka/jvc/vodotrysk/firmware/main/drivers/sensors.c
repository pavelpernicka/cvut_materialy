#include "drivers/sensors.h"

#include <string.h>
#include <time.h>

#include "board/pinmap.h"
#include "drivers/aht20.h"
#include "drivers/rtc_ds3231.h"
#include "driver/gpio.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "system/config.h"

static const char *TAG = "sensors";
static sensor_snapshot_t s_cached;
static adc_oneshot_unit_handle_t s_adc_units[2];
static adc_unit_t s_adc_unit_ids[3];
static adc_channel_t s_adc_channels[3];
static bool s_adc_valid[3];
static bool s_level_stable[2];
static bool s_level_last_raw[2];
static uint64_t s_level_last_change_us[2];

static water_level_state_t sensors_compute_water_state(bool level_low, bool level_high)
{
    if (level_high && !level_low) {
        return WATER_STATE_ERROR;
    }
    if (level_high) {
        return WATER_STATE_HIGH;
    }
    if (level_low) {
        return WATER_STATE_FILLING;
    }
    return WATER_STATE_LOW;
}

static float adc_raw_to_current(int raw)
{
    const app_config_t *cfg = config_get();
    const float voltage = ((float) raw / 4095.0f) * 3.3f;
    const float sense_resistor_ohm = 0.1f;
    const float ina_gain = 50.0f;
    float current = voltage / (sense_resistor_ohm * ina_gain);
    current = current * cfg->sensors.current_adc_scale + cfg->sensors.current_adc_offset;
    return current < 0.0f ? 0.0f : current;
}

static esp_err_t sensors_adc_setup_channel(int pin, size_t index)
{
    adc_unit_t unit = 0;
    adc_channel_t channel = 0;
    esp_err_t err = adc_oneshot_io_to_channel(pin, &unit, &channel);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "GPIO%d is not ADC capable", pin);
        s_adc_valid[index] = false;
        return err;
    }

    size_t unit_index = unit - 1;
    if (s_adc_units[unit_index] == NULL) {
        adc_oneshot_unit_init_cfg_t init_cfg = {
            .unit_id = unit,
            .ulp_mode = ADC_ULP_MODE_DISABLE,
        };
        ESP_RETURN_ON_ERROR(adc_oneshot_new_unit(&init_cfg, &s_adc_units[unit_index]), TAG, "adc new unit failed");
    }

    adc_oneshot_chan_cfg_t chan_cfg = {
        .atten = ADC_ATTEN_DB_12,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    ESP_RETURN_ON_ERROR(adc_oneshot_config_channel(s_adc_units[unit_index], channel, &chan_cfg), TAG, "adc channel config failed");
    s_adc_unit_ids[index] = unit;
    s_adc_channels[index] = channel;
    s_adc_valid[index] = true;
    return ESP_OK;
}

esp_err_t sensors_init(void)
{
    const gpio_config_t cfg = {
        .mode = GPIO_MODE_INPUT,
        .pin_bit_mask = (1ULL << PIN_WATER_LEVEL_1) | (1ULL << PIN_WATER_LEVEL_2),
        .pull_up_en = GPIO_PULLUP_ENABLE,
    };
    ESP_RETURN_ON_ERROR(gpio_config(&cfg), TAG, "level gpio config failed");
    memset(&s_cached, 0, sizeof(s_cached));
    s_level_last_raw[0] = gpio_get_level(PIN_WATER_LEVEL_1) != 0;
    s_level_last_raw[1] = gpio_get_level(PIN_WATER_LEVEL_2) != 0;
    s_level_stable[0] = s_level_last_raw[0];
    s_level_stable[1] = s_level_last_raw[1];
    s_level_last_change_us[0] = esp_timer_get_time();
    s_level_last_change_us[1] = esp_timer_get_time();
    (void) sensors_adc_setup_channel(PIN_CURR_ADC1, 0);
    (void) sensors_adc_setup_channel(PIN_CURR_ADC2, 1);
    (void) sensors_adc_setup_channel(PIN_CURR_ADC3, 2);
    return ESP_OK;
}

esp_err_t sensors_sample(sensor_snapshot_t *out_snapshot)
{
    if (out_snapshot == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    const app_config_t *cfg = config_get();
    const uint64_t now_us = (uint64_t) esp_timer_get_time();
    bool raw_low = gpio_get_level(PIN_WATER_LEVEL_1) != 0;
    bool raw_high = gpio_get_level(PIN_WATER_LEVEL_2) != 0;
    if (cfg->sensors.level_low_invert) {
        raw_low = !raw_low;
    }
    if (cfg->sensors.level_high_invert) {
        raw_high = !raw_high;
    }
    bool raw_levels[2] = { raw_low, raw_high };
    for (size_t i = 0; i < 2; ++i) {
        if (raw_levels[i] != s_level_last_raw[i]) {
            s_level_last_raw[i] = raw_levels[i];
            s_level_last_change_us[i] = now_us;
        }
        if ((now_us - s_level_last_change_us[i]) >= ((uint64_t) cfg->sensors.level_debounce_ms * 1000ULL)) {
            s_level_stable[i] = s_level_last_raw[i];
        }
    }
    s_cached.level_low = s_level_stable[0];
    s_cached.level_high = s_level_stable[1];
    s_cached.water_state = sensors_compute_water_state(s_cached.level_low, s_cached.level_high);
    s_cached.aht20_present = aht20_is_present();
    s_cached.rtc_present = rtc_ds3231_is_present();
    for (size_t i = 0; i < 3; ++i) {
        s_cached.adc_valid[i] = s_adc_valid[i];
        if (s_adc_valid[i]) {
            int raw = 0;
            adc_oneshot_unit_handle_t handle = s_adc_units[s_adc_unit_ids[i] - 1];
            if (adc_oneshot_read(handle, s_adc_channels[i], &raw) == ESP_OK) {
                s_cached.adc_raw[i] = raw;
                s_cached.pump_currents_a[i] = adc_raw_to_current(raw);
            }
        } else {
            s_cached.adc_raw[i] = 0;
        }
    }
    s_cached.history_head = (uint8_t) ((s_cached.history_head + 1U) % SENSOR_HISTORY_LEN);
    for (size_t i = 0; i < 2; ++i) {
        s_cached.pump_current_history_a[i][s_cached.history_head] = s_cached.pump_currents_a[i];
    }
    if (aht20_read(&s_cached.temperature_c, &s_cached.humidity_pct) != ESP_OK) {
        s_cached.temperature_c = 0.0f;
        s_cached.humidity_pct = 0.0f;
    }
    if (rtc_ds3231_get_unix_time(&s_cached.unix_time) != ESP_OK) {
        s_cached.unix_time = (uint64_t) time(NULL);
    }

    *out_snapshot = s_cached;
    return ESP_OK;
}

const sensor_snapshot_t *sensors_get_cached(void)
{
    return &s_cached;
}
