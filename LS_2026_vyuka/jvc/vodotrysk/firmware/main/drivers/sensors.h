#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"

typedef enum {
    WATER_STATE_UNKNOWN = 0,
    WATER_STATE_LOW,
    WATER_STATE_FILLING,
    WATER_STATE_HIGH,
    WATER_STATE_ERROR,
} water_level_state_t;

#define SENSOR_HISTORY_LEN 32

typedef struct {
    bool level_low;
    bool level_high;
    bool aht20_present;
    bool rtc_present;
    bool adc_valid[3];
    int adc_raw[3];
    float pump_currents_a[3];
    float pump_current_history_a[2][SENSOR_HISTORY_LEN];
    uint8_t history_head;
    water_level_state_t water_state;
    float temperature_c;
    float humidity_pct;
    uint64_t unix_time;
} sensor_snapshot_t;

esp_err_t sensors_init(void);
esp_err_t sensors_sample(sensor_snapshot_t *out_snapshot);
const sensor_snapshot_t *sensors_get_cached(void);
