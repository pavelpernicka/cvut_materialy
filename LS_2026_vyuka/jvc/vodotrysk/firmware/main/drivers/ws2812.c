#include "drivers/ws2812.h"

#include <stdbool.h>

#include "board/pinmap.h"
#include "esp_check.h"
#include "esp_log.h"
#include "led_strip.h"

static const char *TAG = "ws2812";
static led_strip_handle_t s_strip;
static rgb_t s_last_color;
static bool s_initialized;

esp_err_t ws2812_init(void)
{
    if (s_initialized) {
        return ESP_OK;
    }

    led_strip_config_t strip_config = {
        .strip_gpio_num = PIN_WS2812B,
        .max_leds = 1,
    };
    led_strip_rmt_config_t rmt_config = {
        .resolution_hz = 10 * 1000 * 1000,
        .flags.with_dma = false,
    };

    ESP_RETURN_ON_ERROR(led_strip_new_rmt_device(&strip_config, &rmt_config, &s_strip), TAG, "create strip failed");
    ESP_RETURN_ON_ERROR(led_strip_clear(s_strip), TAG, "clear strip failed");
    s_last_color = (rgb_t) {0, 0, 0};
    s_initialized = true;
    ESP_LOGI(TAG, "WS2812 initialized on GPIO%d", PIN_WS2812B);
    return ESP_OK;
}

esp_err_t ws2812_set(rgb_t color)
{
    if (!s_initialized || s_strip == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    if (color.r == s_last_color.r && color.g == s_last_color.g && color.b == s_last_color.b) {
        return ESP_OK;
    }
    ESP_RETURN_ON_ERROR(led_strip_set_pixel(s_strip, 0, color.r, color.g, color.b), TAG, "set pixel failed");
    ESP_RETURN_ON_ERROR(led_strip_refresh(s_strip), TAG, "refresh strip failed");
    s_last_color = color;
    return ESP_OK;
}
