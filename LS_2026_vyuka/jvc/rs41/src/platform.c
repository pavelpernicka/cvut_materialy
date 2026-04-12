#include "platform.h"

#include "board.h"

static volatile uint32_t g_millis = 0;

static void gpio_config(GPIO_TypeDef *port, uint8_t pin, uint8_t mode, uint8_t cnf) {
    volatile uint32_t *reg = (pin < 8U) ? &port->CRL : &port->CRH;
    uint8_t pin_shift = (uint8_t) ((pin & 0x7U) * 4U);
    uint32_t value = ((uint32_t) cnf << 2U) | (uint32_t) mode;

    *reg &= ~(0xFUL << pin_shift);
    *reg |= value << pin_shift;
}

void gpio_config_output(GPIO_TypeDef *port, uint8_t pin, uint8_t mode, uint8_t cnf) {
    gpio_config(port, pin, mode, cnf);
}

void gpio_config_input(GPIO_TypeDef *port, uint8_t pin, uint8_t cnf) {
    gpio_config(port, pin, GPIO_MODE_INPUT, cnf);
}

void gpio_write(GPIO_TypeDef *port, uint8_t pin, bool high) {
    if (high) {
        port->BSRR = 1UL << pin;
    } else {
        port->BRR = 1UL << pin;
    }
}

bool gpio_read(GPIO_TypeDef *port, uint8_t pin) {
    return ((port->IDR >> pin) & 0x1U) != 0U;
}

void gpio_toggle(GPIO_TypeDef *port, uint8_t pin) {
    gpio_write(port, pin, !gpio_read(port, pin));
}

void SysTick_Handler(void) {
    g_millis++;
}

uint32_t platform_millis(void) {
    return g_millis;
}

static void spin_cycles(uint32_t cycles) {
    while (cycles-- != 0U) {
        __asm__ volatile ("nop");
    }
}

void delay_us(uint32_t us) {
    spin_cycles(us * (SYSTEM_CORE_CLOCK_HZ / 3000000UL));
}

void delay_ms(uint32_t ms) {
    uint32_t start = platform_millis();
    while ((platform_millis() - start) < ms) {
    }
}

void platform_led_red(bool on) {
    gpio_write(GPIOB, 8U, !on);
}

void platform_led_green(bool on) {
    gpio_write(GPIOB, 7U, !on);
}

void platform_init(void) {
    RCC->APB2ENR |= RCC_APB2ENR_AFIOEN | RCC_APB2ENR_IOPAEN |
                    RCC_APB2ENR_IOPBEN | RCC_APB2ENR_IOPCEN;
    RCC->APB1ENR |= RCC_APB1ENR_SPI2EN | RCC_APB1ENR_USART3EN;
    AFIO->MAPR |= AFIO_MAPR_SWJ_CFG_JTAGDISABLE;

    gpio_config_output(GPIOB, 8U, GPIO_MODE_OUTPUT_2MHZ, GPIO_CNF_GP_PUSHPULL);
    gpio_config_output(GPIOB, 7U, GPIO_MODE_OUTPUT_2MHZ, GPIO_CNF_GP_PUSHPULL);
    gpio_write(GPIOB, 8U, true);
    gpio_write(GPIOB, 7U, true);

    SYSTICK->LOAD = (SYSTEM_CORE_CLOCK_HZ / 1000UL) - 1UL;
    SYSTICK->VAL = 0U;
    SYSTICK->CTRL = SYSTICK_CTRL_CLKSRC | SYSTICK_CTRL_TICKINT | SYSTICK_CTRL_ENABLE;
}
