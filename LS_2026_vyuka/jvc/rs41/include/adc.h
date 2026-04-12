#ifndef ADC_H
#define ADC_H

#include <stdint.h>

void adc_init(void);
uint16_t adc_read_channel(uint8_t channel);
uint16_t adc_read_battery_mv(void);
int16_t adc_read_mcu_temperature_centi(void);

#endif
