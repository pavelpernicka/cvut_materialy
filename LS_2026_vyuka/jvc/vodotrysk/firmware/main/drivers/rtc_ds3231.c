#include "drivers/rtc_ds3231.h"

#include <time.h>

#include "drivers/i2c_bus.h"
#include "esp_check.h"
#include "esp_log.h"

static const char *TAG = "ds3231";
static const uint8_t DS3231_ADDR = 0x68;
static bool s_present;

static int bcd_to_int(uint8_t value)
{
    return ((value >> 4) * 10) + (value & 0x0F);
}

esp_err_t rtc_ds3231_init(void)
{
    if (i2c_bus_init() != ESP_OK) {
        return ESP_FAIL;
    }
    if (i2c_bus_probe(DS3231_ADDR) != ESP_OK) {
        ESP_LOGW(TAG, "DS3231 not detected");
        s_present = false;
        return ESP_ERR_NOT_FOUND;
    }
    s_present = true;
    ESP_LOGI(TAG, "DS3231 detected");
    return ESP_OK;
}

esp_err_t rtc_ds3231_get_unix_time(uint64_t *out_unix_time)
{
    if (out_unix_time == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (!s_present) {
        *out_unix_time = (uint64_t) time(NULL);
        return ESP_ERR_NOT_FOUND;
    }

    static const uint8_t start_reg = 0x00;
    uint8_t raw[7] = {0};
    ESP_RETURN_ON_ERROR(i2c_bus_write_read(DS3231_ADDR, &start_reg, 1, raw, sizeof(raw)), TAG, "RTC read failed");

    struct tm tm_now = {
        .tm_sec = bcd_to_int(raw[0] & 0x7F),
        .tm_min = bcd_to_int(raw[1] & 0x7F),
        .tm_hour = bcd_to_int(raw[2] & 0x3F),
        .tm_mday = bcd_to_int(raw[4] & 0x3F),
        .tm_mon = bcd_to_int(raw[5] & 0x1F) - 1,
        .tm_year = bcd_to_int(raw[6]) + 100,
    };
    *out_unix_time = (uint64_t) mktime(&tm_now);
    return ESP_OK;
}

bool rtc_ds3231_is_present(void)
{
    return s_present;
}
