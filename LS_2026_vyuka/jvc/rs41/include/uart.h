#ifndef UART_H
#define UART_H

#include <stdbool.h>
#include <stdint.h>

void uart1_init(uint32_t baudrate);
bool uart1_read_byte(uint8_t *byte_out);
void uart1_write_byte(uint8_t byte);

#endif
