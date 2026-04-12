#include "uart.h"

#include "board.h"
#include "platform.h"
#include "stm32f100.h"

void uart1_init(uint32_t baudrate) {
    RCC->APB2ENR |= RCC_APB2ENR_USART1EN | RCC_APB2ENR_IOPAEN;

    gpio_config_output(GPIOA, 9U, GPIO_MODE_OUTPUT_50MHZ, GPIO_CNF_AF_PUSHPULL);
    gpio_config_input(GPIOA, 10U, GPIO_CNF_FLOATING);

    USART1->BRR = SYSTEM_CORE_CLOCK_HZ / baudrate;
    USART1->CR1 = USART_CR1_UE | USART_CR1_TE | USART_CR1_RE;
}

bool uart1_read_byte(uint8_t *byte_out) {
    if ((USART1->SR & USART_SR_RXNE) == 0U) {
        return false;
    }

    *byte_out = (uint8_t) USART1->DR;
    return true;
}

void uart1_write_byte(uint8_t byte) {
    while ((USART1->SR & USART_SR_TXE) == 0U) {
    }

    USART1->DR = byte;
}
