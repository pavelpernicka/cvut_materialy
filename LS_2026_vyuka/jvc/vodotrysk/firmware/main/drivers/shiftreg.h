#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"

esp_err_t shiftreg_init(void);
esp_err_t shiftreg_write_u64(uint64_t mask);
void shiftreg_all_off(void);
void shiftreg_enable(bool enable);
void shiftreg_clear(void);
void shiftreg_self_test_chase(uint32_t delay_ms);
void shiftreg_self_test_all_on(uint32_t ms);
