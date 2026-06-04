#include "drivers/i2c_bus.h"

#include <stdbool.h>
#include <string.h>

#include "board/pinmap.h"
#include "driver/i2c_master.h"
#include "esp_check.h"
#include "esp_log.h"

static const char *TAG = "i2c_bus";
static bool s_inited;
static i2c_master_bus_handle_t s_bus;

typedef struct {
    uint8_t address;
    i2c_master_dev_handle_t handle;
} i2c_device_slot_t;

static i2c_device_slot_t s_devices[8];

static esp_err_t get_or_create_device(uint8_t address, i2c_master_dev_handle_t *out_handle)
{
    for (size_t i = 0; i < sizeof(s_devices) / sizeof(s_devices[0]); ++i) {
        if (s_devices[i].handle != NULL && s_devices[i].address == address) {
            *out_handle = s_devices[i].handle;
            return ESP_OK;
        }
    }

    size_t free_index = sizeof(s_devices) / sizeof(s_devices[0]);
    for (size_t i = 0; i < sizeof(s_devices) / sizeof(s_devices[0]); ++i) {
        if (s_devices[i].handle == NULL) {
            free_index = i;
            break;
        }
    }
    if (free_index >= sizeof(s_devices) / sizeof(s_devices[0])) {
        return ESP_ERR_NO_MEM;
    }

    i2c_device_config_t dev_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = address,
        .scl_speed_hz = 100000,
        .scl_wait_us = 0,
        .flags.disable_ack_check = 0,
    };
    ESP_RETURN_ON_ERROR(i2c_master_bus_add_device(s_bus, &dev_cfg, &s_devices[free_index].handle), TAG, "add device failed");
    s_devices[free_index].address = address;
    *out_handle = s_devices[free_index].handle;
    return ESP_OK;
}

esp_err_t i2c_bus_init(void)
{
    if (s_inited) {
        return ESP_OK;
    }

    i2c_master_bus_config_t cfg = {
        .i2c_port = I2C_NUM_0,
        .sda_io_num = PIN_I2C_SDA,
        .scl_io_num = PIN_I2C_SCL,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .intr_priority = 0,
        .trans_queue_depth = 4,
        .flags.enable_internal_pullup = 1,
        .flags.allow_pd = 0,
    };

    ESP_RETURN_ON_ERROR(i2c_new_master_bus(&cfg, &s_bus), TAG, "i2c new bus failed");
    memset(s_devices, 0, sizeof(s_devices));
    s_inited = true;
    ESP_LOGI(TAG, "I2C initialized on SDA=%d SCL=%d", PIN_I2C_SDA, PIN_I2C_SCL);
    return ESP_OK;
}

esp_err_t i2c_bus_probe(uint8_t address)
{
    return i2c_master_probe(s_bus, address, 100);
}

esp_err_t i2c_bus_write(uint8_t address, const uint8_t *data, size_t len)
{
    i2c_master_dev_handle_t handle = NULL;
    ESP_RETURN_ON_ERROR(get_or_create_device(address, &handle), TAG, "device alloc failed");
    return i2c_master_transmit(handle, data, len, 100);
}

esp_err_t i2c_bus_read(uint8_t address, uint8_t *data, size_t len)
{
    i2c_master_dev_handle_t handle = NULL;
    ESP_RETURN_ON_ERROR(get_or_create_device(address, &handle), TAG, "device alloc failed");
    return i2c_master_receive(handle, data, len, 100);
}

esp_err_t i2c_bus_write_read(uint8_t address, const uint8_t *wr, size_t wr_len, uint8_t *rd, size_t rd_len)
{
    i2c_master_dev_handle_t handle = NULL;
    ESP_RETURN_ON_ERROR(get_or_create_device(address, &handle), TAG, "device alloc failed");
    return i2c_master_transmit_receive(handle, wr, wr_len, rd, rd_len, 100);
}
