#include "drivers/rtc_ds3231.h"

#include <sys/time.h>
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

static uint8_t int_to_bcd(int value)
{
    return (uint8_t) (((value / 10) << 4) | (value % 10));
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

esp_err_t rtc_ds3231_set_unix_time(uint64_t unix_time)
{
    struct timeval tv = {
        .tv_sec = (time_t) unix_time,
        .tv_usec = 0,
    };
    (void) settimeofday(&tv, NULL);

    if (!s_present) {
        return ESP_ERR_NOT_FOUND;
    }

    time_t now = (time_t) unix_time;
    struct tm tm_now = {0};
    localtime_r(&now, &tm_now);

    uint8_t raw[8] = {
        0x00,
        int_to_bcd(tm_now.tm_sec),
        int_to_bcd(tm_now.tm_min),
        int_to_bcd(tm_now.tm_hour),
        int_to_bcd(tm_now.tm_wday == 0 ? 7 : tm_now.tm_wday),
        int_to_bcd(tm_now.tm_mday),
        int_to_bcd(tm_now.tm_mon + 1),
        int_to_bcd((tm_now.tm_year + 1900) % 100),
    };
    ESP_RETURN_ON_ERROR(i2c_bus_write(DS3231_ADDR, raw, sizeof(raw)), TAG, "RTC write failed");
    return ESP_OK;
}

bool rtc_ds3231_is_present(void)
{
    return s_present;
}
