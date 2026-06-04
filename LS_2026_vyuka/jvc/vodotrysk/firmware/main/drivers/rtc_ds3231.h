#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"

esp_err_t rtc_ds3231_init(void);
esp_err_t rtc_ds3231_get_unix_time(uint64_t *out_unix_time);
bool rtc_ds3231_is_present(void);
