#pragma once

#include <stddef.h>
#include <stdint.h>

#include "esp_err.h"

esp_err_t i2c_bus_init(void);
esp_err_t i2c_bus_probe(uint8_t address);
esp_err_t i2c_bus_write(uint8_t address, const uint8_t *data, size_t len);
esp_err_t i2c_bus_read(uint8_t address, uint8_t *data, size_t len);
esp_err_t i2c_bus_write_read(uint8_t address, const uint8_t *wr, size_t wr_len, uint8_t *rd, size_t rd_len);
