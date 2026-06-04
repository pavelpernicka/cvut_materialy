#include "system/safety.h"

#include "board/pinmap.h"
#include "driver/gpio.h"
#include "drivers/pumps.h"
#include "drivers/shiftreg.h"
#include "esp_log.h"

static const char *TAG = "safety";

esp_err_t safety_pre_init(void)
{
    const gpio_config_t cfg = {
        .mode = GPIO_MODE_OUTPUT,
        .pin_bit_mask = (1ULL << PIN_SR_LATCH_CLK) | (1ULL << PIN_SR_CLEAR) | (1ULL << PIN_SR_ENABLE),
    };
    ESP_ERROR_CHECK(gpio_config(&cfg));
    gpio_set_level(PIN_SR_LATCH_CLK, 0);
    shiftreg_enable(false);
    shiftreg_clear();
    ESP_LOGI(TAG, "Outputs forced to safe state before init");
    return ESP_OK;
}

esp_err_t safety_emergency_all_off(const char *reason)
{
    shiftreg_enable(false);
    shiftreg_all_off();
    pumps_all_off();
    ESP_LOGE(TAG, "Emergency all-off: %s", reason == NULL ? "unknown" : reason);
    return ESP_OK;
}
