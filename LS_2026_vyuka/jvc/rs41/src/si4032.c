#include "si4032.h"

#include <stddef.h>
#include <stdint.h>

#include "board.h"
#include "platform.h"
#include "spi.h"

enum {
    SI4032_DIRECT_FSK = 0x12U,
    MODULATION_TIMER_HZ = 1000000U,
    BIT_PERIOD_BASE_US = 1000000U / RF_BITRATE_BPS,
    BIT_PERIOD_REMAINDER = 1000000U % RF_BITRATE_BPS,
    SI4032_MAX_PACKET_BYTES = 64U,
};

static void radio_select(uint8_t select) {
    gpio_write(GPIOC, 13U, select == 0U);
}

static uint8_t read_register(uint8_t address) {
    uint8_t value;

    radio_select(1U);
    (void) spi2_transfer((uint8_t) (address & 0x7FU));
    value = spi2_transfer(0x00U);
    radio_select(0U);

    return value;
}

static void write_register(uint8_t address, uint8_t data) {
    radio_select(1U);
    (void) spi2_transfer((uint8_t) (address | 0x80U));
    (void) spi2_transfer(data);
    radio_select(0U);
}

static void clear_interrupts(void) {
    (void) read_register(0x03U);
    (void) read_register(0x04U);
}

static void enable_tx(void) {
    write_register(0x07U, 0x0BU);
}

static void inhibit_tx(void) {
    write_register(0x07U, 0x03U);
}

static void use_direct_mode(uint8_t use) {
    radio_select(use);
}

static void set_modulation_direct_fsk(void) {
    write_register(0x70U, 0x20U);
    write_register(0x71U, SI4032_DIRECT_FSK);
    write_register(0x72U, RF_DEVIATION_LEVEL);
    write_register(0x73U, 0x00U);
    write_register(0x74U, 0x00U);
    write_register(0x30U, 0x00U);
}

static void modulation_pin_write(uint8_t high) {
    gpio_write(GPIOB, 15U, high != 0U);
}

static void modulation_pin_init(void) {
    RCC->APB2ENR |= RCC_APB2ENR_IOPBEN | RCC_APB2ENR_TIM15EN;
    SPI2->CR1 &= ~SPI_CR1_SPE;
    gpio_config_output(GPIOB, 15U, GPIO_MODE_OUTPUT_50MHZ, GPIO_CNF_GP_PUSHPULL);
    modulation_pin_write(0U);

    TIM15->CR1 = 0x00U;
    TIM15->CR2 = 0x00U;
    TIM15->SMCR = 0x00U;
    TIM15->DIER = 0x00U;
    TIM15->SR = 0x00U;
    TIM15->CCER = 0x00U;
    TIM15->CCMR1 = 0x00U;
    TIM15->PSC = (SYSTEM_CORE_CLOCK_HZ / MODULATION_TIMER_HZ) - 1U;
    TIM15->ARR = 0xFFFFU;
    TIM15->CNT = 0x0000U;
    TIM15->RCR = 0x00U;
    TIM15->BDTR = 0x00U;
    TIM15->EGR = TIM_EGR_UG;
    TIM15->CR1 = TIM_CR1_CEN;
}

static void modulation_pin_uninit(void) {
    TIM15->CR1 = 0x00U;
    RCC->APB2ENR &= ~RCC_APB2ENR_TIM15EN;
    modulation_pin_write(0U);
}

static void modulation_wait_us(uint16_t duration_us) {
    uint16_t start = (uint16_t) TIM15->CNT;

    while ((uint16_t) (TIM15->CNT - start) < duration_us) {
    }
}

static void transmit_bit(uint8_t bit_value, uint16_t *timing_error_accum) {
    modulation_pin_write(bit_value);
    modulation_wait_us(BIT_PERIOD_BASE_US);

    *timing_error_accum = (uint16_t) (*timing_error_accum + BIT_PERIOD_REMAINDER);
    if (*timing_error_accum >= RF_BITRATE_BPS) {
        modulation_wait_us(1U);
        *timing_error_accum = (uint16_t) (*timing_error_accum - RF_BITRATE_BPS);
    }
}

static void transmit_byte(uint8_t byte, uint16_t *timing_error_accum) {
    for (uint8_t bit = 0U; bit < 8U; ++bit) {
        transmit_bit((uint8_t) ((byte & 0x80U) != 0U), timing_error_accum);
        byte <<= 1U;
    }
}

static void transmit_frame(const uint8_t *payload, size_t length) {
    uint16_t timing_error_accum = 0U;

    modulation_pin_write(0U);

    for (uint8_t i = 0U; i < RF_PREAMBLE_BYTES; ++i) {
        transmit_byte(0xAAU, &timing_error_accum);
    }

    transmit_byte(RF_SYNC_WORD_0, &timing_error_accum);
    transmit_byte(RF_SYNC_WORD_1, &timing_error_accum);

    for (size_t i = 0U; i < length; ++i) {
        transmit_byte(payload[i], &timing_error_accum);
    }

    modulation_pin_write(0U);
}

void si4032_set_frequency(float frequency_mhz) {
    uint8_t hbsel = (uint8_t) (((frequency_mhz * (30.0f / 26.0f)) >= 480.0f) ? 1U : 0U);
    uint8_t fb = (uint8_t) (((((uint8_t) ((frequency_mhz * (30.0f / 26.0f)) / 10.0f)) - 24U) - (24U * hbsel)) / (1U + hbsel));
    uint16_t fc = (uint16_t) (((frequency_mhz / ((26.0f / 3.0f) * (hbsel + 1U))) - fb - 24.0f) * 64000.0f);

    write_register(0x75U, (uint8_t) (0x40U | (fb & 0x1FU) | ((hbsel & 0x1U) << 5U)));
    write_register(0x76U, (uint8_t) ((fc >> 8U) & 0xFFU));
    write_register(0x77U, (uint8_t) (fc & 0xFFU));
}

void si4032_set_power(uint8_t level) {
    write_register(0x6DU, (uint8_t) (level & 0x07U));
}

void si4032_init(void) {
    delay_ms(20U);

    write_register(0x06U, 0x00U);
    write_register(0x07U, 0x01U);
    write_register(0x08U, 0x00U);
    write_register(0x09U, 0x7FU);
    write_register(0x0AU, 0x05U);
    write_register(0x0BU, 0xF4U);
    write_register(0x0CU, 0xEFU);
    write_register(0x0DU, 0x00U);
    write_register(0x0EU, 0x00U);
    write_register(0x0FU, 0x80U);
    write_register(0x10U, 0x00U);
    write_register(0x12U, 0x20U);
    write_register(0x13U, 0x00U);
    write_register(0x1CU, 0x1DU);
    write_register(0x1DU, 0x40U);
    write_register(0x20U, 0xA1U);
    write_register(0x21U, 0x20U);
    write_register(0x22U, 0x4EU);
    write_register(0x23U, 0xA5U);
    write_register(0x24U, 0x00U);
    write_register(0x25U, 0x0AU);
    write_register(0x43U, 0x00U);
    write_register(0x44U, 0x00U);
    write_register(0x45U, 0x00U);
    write_register(0x46U, 0x00U);
    write_register(0x79U, 0x00U);
    write_register(0x7AU, 0x00U);

    set_modulation_direct_fsk();
    si4032_set_power(RF_POWER_LEVEL);
    si4032_set_frequency(RF_FREQUENCY_MHZ);
    clear_interrupts();
    inhibit_tx();
    use_direct_mode(0U);
}

void si4032_transmit_packet(const uint8_t *payload, size_t length) {
    uint32_t systick_ctrl;

    if (payload == NULL || length == 0U || length > SI4032_MAX_PACKET_BYTES) {
        return;
    }

    si4032_init();

    for (uint8_t repeat = 0U; repeat < RF_PACKET_REPEATS; ++repeat) {
        enable_tx();
        modulation_pin_init();
        use_direct_mode(1U);

        systick_ctrl = SYSTICK->CTRL;
        SYSTICK->CTRL = systick_ctrl & ~SYSTICK_CTRL_TICKINT;

        transmit_frame(payload, length);

        SYSTICK->CTRL = systick_ctrl;
        use_direct_mode(0U);
        modulation_pin_uninit();
        spi2_init();
        inhibit_tx();
        clear_interrupts();

        if ((repeat + 1U) < RF_PACKET_REPEATS) {
            delay_ms(RF_INTER_PACKET_GAP_MS);
        }
    }
}
