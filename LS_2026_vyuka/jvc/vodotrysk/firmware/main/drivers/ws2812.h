#pragma once

#include <stdint.h>

#include "esp_err.h"

typedef struct {
    uint8_t r;
    uint8_t g;
    uint8_t b;
} rgb_t;

esp_err_t ws2812_init(void);
esp_err_t ws2812_set(rgb_t color);
