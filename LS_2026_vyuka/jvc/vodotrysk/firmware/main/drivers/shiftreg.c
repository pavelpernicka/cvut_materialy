#include "drivers/shiftreg.h"

#include <string.h>

#include "board/board_config.h"
#include "board/pinmap.h"
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_rom_sys.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "shiftreg";
static spi_device_handle_t s_spi;
static bool s_inited;

static void shiftreg_latch(void)
{
    gpio_set_level(PIN_SR_LATCH_CLK, 1);
    esp_rom_delay_us(1);
    gpio_set_level(PIN_SR_LATCH_CLK, 0);
}

void shiftreg_enable(bool enable)
{
    gpio_set_level(PIN_SR_ENABLE, enable ? 0 : 1);
}

void shiftreg_clear(void)
{
    gpio_set_level(PIN_SR_CLEAR, 0);
    esp_rom_delay_us(1);
    gpio_set_level(PIN_SR_CLEAR, 1);
}

void shiftreg_all_off(void)
{
    if (s_inited) {
        (void) shiftreg_write_u64(0);
    } else {
        shiftreg_enable(false);
        shiftreg_clear();
    }
}

esp_err_t shiftreg_init(void)
{
    const gpio_config_t out_cfg = {
        .mode = GPIO_MODE_OUTPUT,
        .pin_bit_mask = (1ULL << PIN_SR_LATCH_CLK) | (1ULL << PIN_SR_CLEAR) | (1ULL << PIN_SR_ENABLE),
    };
    ESP_RETURN_ON_ERROR(gpio_config(&out_cfg), TAG, "gpio_config failed");

    gpio_set_level(PIN_SR_LATCH_CLK, 0);
    gpio_set_level(PIN_SR_CLEAR, 1);
    shiftreg_enable(false);
    shiftreg_clear();

    spi_bus_config_t buscfg = {
        .mosi_io_num = PIN_SR_DATA,
        .miso_io_num = -1,
        .sclk_io_num = PIN_SR_SHIFT_CLK,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = 8,
    };
    ESP_RETURN_ON_ERROR(spi_bus_initialize(SPI2_HOST, &buscfg, SPI_DMA_CH_AUTO), TAG, "spi bus init failed");

    spi_device_interface_config_t devcfg = {
        .clock_speed_hz = 1 * 1000 * 1000,
        .mode = 0,
        .spics_io_num = -1,
        .queue_size = 1,
    };
    ESP_RETURN_ON_ERROR(spi_bus_add_device(SPI2_HOST, &devcfg, &s_spi), TAG, "spi add device failed");

    s_inited = true;
    shiftreg_all_off();
    ESP_LOGI(TAG, "74HC595 chain initialized");
    return ESP_OK;
}

esp_err_t shiftreg_write_u64(uint64_t mask)
{
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }

    const board_config_t *board = board_config_get();
    uint8_t tx[8];
    for (size_t i = 0; i < sizeof(tx); ++i) {
        size_t shift = board->shift_msb_first ? (56 - (i * 8)) : (i * 8);
        tx[i] = (uint8_t) ((mask >> shift) & 0xffU);
        if (board->invert_shift_outputs) {
            tx[i] = (uint8_t) ~tx[i];
        }
    }

    spi_transaction_t t = {
        .length = sizeof(tx) * 8,
        .tx_buffer = tx,
    };
    ESP_RETURN_ON_ERROR(spi_device_transmit(s_spi, &t), TAG, "spi transmit failed");
    shiftreg_latch();
    return ESP_OK;
}

void shiftreg_self_test_chase(uint32_t delay_ms)
{
    for (uint32_t i = 0; i < 64; ++i) {
        (void) shiftreg_write_u64(1ULL << i);
        vTaskDelay(pdMS_TO_TICKS(delay_ms));
    }
    shiftreg_all_off();
}

void shiftreg_self_test_all_on(uint32_t ms)
{
    (void) shiftreg_write_u64(UINT64_MAX);
    vTaskDelay(pdMS_TO_TICKS(ms));
    shiftreg_all_off();
}
