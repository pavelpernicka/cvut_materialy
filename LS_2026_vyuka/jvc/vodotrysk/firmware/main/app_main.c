#include "drivers/aht20.h"
#include "drivers/pumps.h"
#include "drivers/rtc_ds3231.h"
#include "drivers/sensors.h"
#include "drivers/shiftreg.h"
#include "drivers/ws2812.h"
#include "engine/queue.h"
#include "engine/show_model.h"
#include "engine/water_engine.h"
#include "esp_check.h"
#include "esp_log.h"
#include "system/config.h"
#include "system/diagnostics.h"
#include "system/logger.h"
#include "system/safety.h"
#include "system/storage.h"
#include "system/web_server.h"
#include "system/websocket.h"
#include "system/wifi_manager.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "board/pinmap.h"

static const char *TAG = "app";
static const BaseType_t APP_CORE_IO = 0;

static void boot_blink_user_led(void)
{
    const gpio_config_t cfg = {
        .pin_bit_mask = 1ULL << PIN_LED_INT,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };

    ESP_ERROR_CHECK(gpio_config(&cfg));

    for (int i = 0; i < 4; ++i) {
        gpio_set_level(PIN_LED_INT, 1);
        vTaskDelay(pdMS_TO_TICKS(300));
        gpio_set_level(PIN_LED_INT, 0);
        vTaskDelay(pdMS_TO_TICKS(300));
    }
}

static rgb_t rgb_scale(rgb_t color, uint8_t scale)
{
    rgb_t out = {
        .r = (uint8_t) ((uint16_t) color.r * scale / 255U),
        .g = (uint8_t) ((uint16_t) color.g * scale / 255U),
        .b = (uint8_t) ((uint16_t) color.b * scale / 255U),
    };
    return out;
}

static rgb_t rgb_for_status(uint32_t tick_ms)
{
    water_engine_status_t engine = water_engine_get_status();
    const sensor_snapshot_t *sensors = sensors_get_cached();
    size_t queued = queue_len();
    uint8_t phase = (uint8_t) ((tick_ms / 20U) % 256U);
    uint8_t breathe = phase < 128 ? (uint8_t) (80 + phase) : (uint8_t) (80 + (255 - phase));

    if (engine.state == WATER_ENGINE_ERROR || engine.state == WATER_ENGINE_EMERGENCY_STOP ||
        sensors->water_state == WATER_STATE_ERROR) {
        return rgb_scale((rgb_t) {255, 0, 0}, breathe);
    }
    if (queued > 0 || engine.state == WATER_ENGINE_PLAYING_GUEST_ITEM) {
        return rgb_scale((rgb_t) {255, 0, 180}, breathe);
    }
    if (engine.state == WATER_ENGINE_PAUSED) {
        return rgb_scale((rgb_t) {255, 90, 0}, breathe);
    }
    if (sensors->water_state == WATER_STATE_LOW || sensors->water_state == WATER_STATE_FILLING) {
        return rgb_scale((rgb_t) {0, 60, 255}, breathe);
    }
    if (engine.state == WATER_ENGINE_PLAYING_SHOW) {
        return rgb_scale((rgb_t) {0, 220, 140}, breathe);
    }
    return rgb_scale((rgb_t) {20, 20, 20}, 140);
}

static void sensor_task(void *arg)
{
    (void) arg;
    sensor_snapshot_t *snapshot = calloc(1, sizeof(sensor_snapshot_t));
    if (snapshot == NULL) {
        vTaskDelete(NULL);
        return;
    }

    while (true) {
        if (sensors_sample(snapshot) == ESP_OK) {
            (void) pumps_set_current(0, snapshot->pump_currents_a[0]);
            (void) pumps_set_current(1, snapshot->pump_currents_a[1]);
            (void) pumps_update_from_levels(snapshot);
        }
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

static void led_task(void *arg)
{
    (void) arg;

    uint32_t tick_ms = 0;
    while (true) {
        (void) ws2812_set(rgb_for_status(tick_ms));
        vTaskDelay(pdMS_TO_TICKS(80));
        tick_ms += 80;
    }
}

void app_main(void)
{
    app_config_t config;
    TaskHandle_t sensor_task_handle = NULL;
    TaskHandle_t led_task_handle = NULL;
    esp_err_t err = ESP_OK;

    logger_init();
    boot_blink_user_led();
    logger_event(LOG_CAT_SYSTEM, "firmware boot start");
    diagnostics_log_boot();
    ESP_ERROR_CHECK(safety_pre_init());
    ESP_ERROR_CHECK(storage_init());
    ESP_ERROR_CHECK(storage_load_config(&config));
    config_set(&config);
    show_model_init();

    ESP_ERROR_CHECK(shiftreg_init());
    ESP_ERROR_CHECK(pumps_init());
    ESP_ERROR_CHECK(sensors_init());
    ESP_ERROR_CHECK(ws2812_init());
    err = aht20_init();
    if (err != ESP_OK && err != ESP_ERR_NOT_FOUND) {
        ESP_ERROR_CHECK(err);
    }
    err = rtc_ds3231_init();
    if (err != ESP_OK && err != ESP_ERR_NOT_FOUND) {
        ESP_ERROR_CHECK(err);
    }
    ESP_ERROR_CHECK(queue_init(config.exhibition.max_queue));
    ESP_ERROR_CHECK(water_engine_init());
    ESP_ERROR_CHECK(wifi_manager_init());
    ESP_ERROR_CHECK(websocket_init());
    ESP_ERROR_CHECK(web_server_start());
    xTaskCreatePinnedToCore(sensor_task, "sensor_task", 6144, NULL, 4, &sensor_task_handle, APP_CORE_IO);
    xTaskCreatePinnedToCore(led_task, "led_task", 3072, NULL, 2, &led_task_handle, APP_CORE_IO);
    diagnostics_register_task(DIAG_TASK_SENSOR, sensor_task_handle, APP_CORE_IO);
    diagnostics_register_task(DIAG_TASK_LED, led_task_handle, APP_CORE_IO);

    shiftreg_enable(true);
    ESP_ERROR_CHECK(water_engine_start());
    logger_event(LOG_CAT_SYSTEM, "system ready");
    ESP_LOGI(TAG, "System ready");

    while (true) {
        vTaskDelay(portMAX_DELAY);
    }
}
