#include "si4032.h"

#include <stdbool.h>
#include <stddef.h>

#include "board.h"
#include "platform.h"
#include "spi.h"

enum {
    SI4032_AX25_FLAG = 0x7E,
    SI4032_DIRECT_FSK = 0x12,
    SI4032_TX_DEVIATION = 0x05,
    BELL202_MARK_HZ = 1200U,
    BELL202_SPACE_HZ = 2200U,
    AX25_SYMBOL_US = 833U,
    TIM15_TICK_HZ = 1000000U,
};

static void radio_select(bool select) {
    gpio_write(GPIOC, 13U, !select);
}

static uint8_t read_register(uint8_t address) {
    uint8_t value;

    radio_select(true);
    (void) spi2_transfer((uint8_t) (address & 0x7FU));
    value = spi2_transfer(0x00U);
    radio_select(false);

    return value;
}

static void write_register(uint8_t address, uint8_t data) {
    radio_select(true);
    (void) spi2_transfer((uint8_t) (address | 0x80U));
    (void) spi2_transfer(data);
    radio_select(false);
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

static void use_direct_mode(bool use) {
    gpio_write(GPIOC, 13U, !use);
}

static void set_modulation_direct_fsk(void) {
    write_register(0x71U, SI4032_DIRECT_FSK);
    write_register(0x72U, SI4032_TX_DEVIATION);
    write_register(0x73U, 0x00U);
    write_register(0x74U, 0x00U);
    write_register(0x30U, 0x00U);
}

static uint16_t pwm_period_for_tone(uint32_t tone_hz) {
    return (uint16_t) (((TIM15_TICK_HZ + tone_hz) / (tone_hz * 2U)) - 1U);
}

static void pwm_timer_use(bool use) {
    if (use) {
        AFIO->MAPR2 |= AFIO_MAPR2_TIM15_REMAP;
    } else {
        AFIO->MAPR2 &= ~AFIO_MAPR2_TIM15_REMAP;
    }
}

static void pwm_timer_set_period(uint16_t period) {
    TIM15->ARR = period;
}

static void pwm_timer_enable_output(bool enable) {
    if (enable) {
        TIM15->BDTR |= TIM_BDTR_MOE;
    } else {
        TIM15->BDTR &= ~TIM_BDTR_MOE;
    }
}

static void pwm_timer_init(uint16_t period) {
    RCC->APB2ENR |= RCC_APB2ENR_AFIOEN | RCC_APB2ENR_IOPBEN | RCC_APB2ENR_TIM15EN;
    SPI2->CR1 &= ~SPI_CR1_SPE;
    pwm_timer_use(true);
    gpio_config_output(GPIOB, 15U, GPIO_MODE_OUTPUT_50MHZ, GPIO_CNF_AF_PUSHPULL);

    TIM15->CR1 = 0x00U;
    TIM15->CR2 = 0x00U;
    TIM15->SMCR = 0x00U;
    TIM15->DIER = 0x00U;
    TIM15->SR = 0x00U;
    TIM15->CCER = 0x00U;
    TIM15->CCMR1 = 0x00U;
    TIM15->PSC = (SYSTEM_CORE_CLOCK_HZ / TIM15_TICK_HZ) - 1U;
    TIM15->ARR = period;
    TIM15->RCR = 0x00U;
    TIM15->CCR2 = 0x00U;
    TIM15->BDTR = 0x00U;
    TIM15->EGR = TIM_EGR_UG;
    TIM15->CCMR1 = TIM_CCMR1_OC2FE | TIM_CCMR1_OC2M_0 | TIM_CCMR1_OC2M_1;
    TIM15->CCER = TIM_CCER_CC2E;
    TIM15->CR1 = TIM_CR1_ARPE | TIM_CR1_CEN;
    pwm_timer_enable_output(true);
}

static void pwm_timer_uninit(void) {
    pwm_timer_enable_output(false);
    TIM15->CR1 = 0x00U;
    TIM15->CCER = 0x00U;
    gpio_config_output(GPIOB, 15U, GPIO_MODE_OUTPUT_50MHZ, GPIO_CNF_GP_PUSHPULL);
    gpio_write(GPIOB, 15U, false);
    pwm_timer_use(false);
    RCC->APB2ENR &= ~RCC_APB2ENR_TIM15EN;
}

static void bell_emit_symbol(bool mark_tone) {
    pwm_timer_set_period(pwm_period_for_tone(mark_tone ? BELL202_MARK_HZ : BELL202_SPACE_HZ));
    delay_us(AX25_SYMBOL_US);
}

static void bell_emit_bit(bool *mark_tone, bool bit) {
    if (!bit) {
        *mark_tone = !*mark_tone;
    }

    bell_emit_symbol(*mark_tone);
}

static void bell_emit_byte(bool *mark_tone, uint8_t byte, bool apply_bit_stuffing, uint8_t *ones_run) {
    for (uint8_t bit_index = 0U; bit_index < 8U; ++bit_index) {
        bool bit = ((byte >> bit_index) & 0x01U) != 0U;

        bell_emit_bit(mark_tone, bit);

        if (!apply_bit_stuffing) {
            *ones_run = 0U;
            continue;
        }

        if (bit) {
            *ones_run += 1U;
            if (*ones_run >= 5U) {
                bell_emit_bit(mark_tone, false);
                *ones_run = 0U;
            }
        } else {
            *ones_run = 0U;
        }
    }
}

static void transmit_bell202_ax25(const uint8_t *payload, size_t length) {
    bool mark_tone = true;
    uint8_t ones_run = 0U;

    for (uint8_t i = 0U; i < AX25_PREAMBLE_FLAGS; ++i) {
        bell_emit_byte(&mark_tone, SI4032_AX25_FLAG, false, &ones_run);
    }

    for (size_t i = 0U; i < length; ++i) {
        bell_emit_byte(&mark_tone, payload[i], payload[i] != SI4032_AX25_FLAG, &ones_run);
    }
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
    write_register(0x6DU, (uint8_t) (level & 0x7U));
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
    use_direct_mode(false);
    inhibit_tx();
}

void si4032_transmit_aprs(const uint8_t *payload, size_t length) {
    if (payload == NULL || length == 0U) {
        return;
    }

    si4032_init();
    pwm_timer_init(pwm_period_for_tone(BELL202_MARK_HZ));
    enable_tx();
    use_direct_mode(true);

    transmit_bell202_ax25(payload, length);

    use_direct_mode(false);
    pwm_timer_uninit();
    inhibit_tx();
    clear_interrupts();
    spi2_init();
}
