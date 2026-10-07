#include "drivers/aht20.h"

#include "drivers/i2c_bus.h"
#include "esp_check.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "aht20";
static const uint8_t AHT20_ADDR = 0x38;
static bool s_present;

static esp_err_t aht20_read_status(uint8_t *out_status)
{
    uint8_t status = 0;
    ESP_RETURN_ON_ERROR(i2c_bus_read(AHT20_ADDR, &status, 1), TAG, "AHT20 status read failed");
    *out_status = status;
    return ESP_OK;
}

esp_err_t aht20_init(void)
{
    static const uint8_t reset_cmd[] = {0xBA};
    static const uint8_t init_cmd[] = {0xBE, 0x08, 0x00};
    if (i2c_bus_init() != ESP_OK) {
        return ESP_FAIL;
    }
    if (i2c_bus_probe(AHT20_ADDR) != ESP_OK) {
        ESP_LOGW(TAG, "AHT20 not detected");
        s_present = false;
        return ESP_ERR_NOT_FOUND;
    }
    s_present = true;
    (void) i2c_bus_write(AHT20_ADDR, reset_cmd, sizeof(reset_cmd));
    vTaskDelay(pdMS_TO_TICKS(25));
    uint8_t status = 0;
    if (aht20_read_status(&status) != ESP_OK) {
        s_present = false;
        return ESP_FAIL;
    }
    if ((status & 0x08U) == 0U) {
        ESP_RETURN_ON_ERROR(i2c_bus_write(AHT20_ADDR, init_cmd, sizeof(init_cmd)), TAG, "AHT20 init failed");
        vTaskDelay(pdMS_TO_TICKS(10));
    }
    ESP_LOGI(TAG, "AHT20 detected");
    return ESP_OK;
}

esp_err_t aht20_read(float *out_temp_c, float *out_humidity_pct)
{
    if (out_temp_c == NULL || out_humidity_pct == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (!s_present) {
        return ESP_ERR_NOT_FOUND;
    }

    static const uint8_t measure_cmd[] = {0xAC, 0x33, 0x00};
    uint8_t data[7] = {0};
    ESP_RETURN_ON_ERROR(i2c_bus_write(AHT20_ADDR, measure_cmd, sizeof(measure_cmd)), TAG, "AHT20 trigger failed");
    for (int retry = 0; retry < 10; ++retry) {
        vTaskDelay(pdMS_TO_TICKS(10));
        ESP_RETURN_ON_ERROR(i2c_bus_read(AHT20_ADDR, data, sizeof(data)), TAG, "AHT20 read failed");
        if ((data[0] & 0x80U) == 0U) {
            uint32_t humidity_raw = ((uint32_t) data[1] << 12) | ((uint32_t) data[2] << 4) | ((uint32_t) data[3] >> 4);
            uint32_t temp_raw = (((uint32_t) data[3] & 0x0F) << 16) | ((uint32_t) data[4] << 8) | data[5];
            *out_humidity_pct = ((float) humidity_raw * 100.0f) / 1048576.0f;
            *out_temp_c = ((float) temp_raw * 200.0f) / 1048576.0f - 50.0f;
            if (*out_humidity_pct < 0.0f) *out_humidity_pct = 0.0f;
            if (*out_humidity_pct > 100.0f) *out_humidity_pct = 100.0f;
            if (*out_temp_c < -40.0f) *out_temp_c = -40.0f;
            if (*out_temp_c > 125.0f) *out_temp_c = 125.0f;
            return ESP_OK;
        }
    }
    return ESP_ERR_TIMEOUT;
}

bool aht20_is_present(void)
{
    return s_present;
}
