#pragma once

#include "esp_err.h"

esp_err_t safety_pre_init(void);
esp_err_t safety_emergency_all_off(const char *reason);
