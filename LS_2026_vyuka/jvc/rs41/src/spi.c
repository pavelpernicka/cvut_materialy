#include "spi.h"

#include "platform.h"
#include "stm32f100.h"

void spi2_init(void) {
    RCC->APB2ENR |= RCC_APB2ENR_IOPBEN | RCC_APB2ENR_IOPCEN;
    RCC->APB1ENR |= RCC_APB1ENR_SPI2EN;

    gpio_config_output(GPIOB, 13U, GPIO_MODE_OUTPUT_50MHZ, GPIO_CNF_AF_PUSHPULL);
    gpio_config_input(GPIOB, 14U, GPIO_CNF_FLOATING);
    gpio_config_output(GPIOB, 15U, GPIO_MODE_OUTPUT_50MHZ, GPIO_CNF_AF_PUSHPULL);
    gpio_config_output(GPIOC, 13U, GPIO_MODE_OUTPUT_10MHZ, GPIO_CNF_GP_PUSHPULL);
    gpio_write(GPIOC, 13U, true);

    SPI2->CR1 = SPI_CR1_MSTR | SPI_CR1_BR_DIV16 | SPI_CR1_SSM | SPI_CR1_SSI | SPI_CR1_SPE;
}

uint8_t spi2_transfer(uint8_t value) {
    while ((SPI2->SR & SPI_SR_TXE) == 0U) {
    }

    SPI2->DR = value;

    while ((SPI2->SR & SPI_SR_RXNE) == 0U) {
    }

    return (uint8_t) SPI2->DR;
}
