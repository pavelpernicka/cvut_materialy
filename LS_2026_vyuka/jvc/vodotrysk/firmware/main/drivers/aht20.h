#pragma once

#include <stdbool.h>

#include "esp_err.h"

esp_err_t aht20_init(void);
esp_err_t aht20_read(float *out_temp_c, float *out_humidity_pct);
bool aht20_is_present(void);
