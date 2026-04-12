#ifndef PLATFORM_H
#define PLATFORM_H

#include <stdbool.h>
#include <stdint.h>

#include "stm32f100.h"

void platform_init(void);
uint32_t platform_millis(void);
void delay_ms(uint32_t ms);
void delay_us(uint32_t us);

void gpio_config_output(GPIO_TypeDef *port, uint8_t pin, uint8_t mode, uint8_t cnf);
void gpio_config_input(GPIO_TypeDef *port, uint8_t pin, uint8_t cnf);
void gpio_write(GPIO_TypeDef *port, uint8_t pin, bool high);
bool gpio_read(GPIO_TypeDef *port, uint8_t pin);
void gpio_toggle(GPIO_TypeDef *port, uint8_t pin);

void platform_led_red(bool on);
void platform_led_green(bool on);

#endif
