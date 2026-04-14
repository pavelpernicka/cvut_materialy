#ifndef SI4032_H
#define SI4032_H

#include <stddef.h>
#include <stdint.h>

void si4032_init(void);
void si4032_set_frequency(float frequency_mhz);
void si4032_set_power(uint8_t level);
void si4032_transmit_packet(const uint8_t *payload, size_t length);

#endif
