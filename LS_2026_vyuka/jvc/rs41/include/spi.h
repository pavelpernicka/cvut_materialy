#ifndef SPI_H
#define SPI_H

#include <stdint.h>

void spi2_init(void);
uint8_t spi2_transfer(uint8_t value);

#endif
