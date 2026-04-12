#include "adc.h"

#include "board.h"
#include "platform.h"
#include "stm32f100.h"

static void adc_set_sample_time(uint8_t channel) {
    if (channel < 10U) {
        uint32_t shift = (uint32_t) channel * 3U;
        ADC1->SMPR2 &= ~(0x7UL << shift);
        ADC1->SMPR2 |= 0x7UL << shift;
    } else {
        uint32_t shift = (uint32_t) (channel - 10U) * 3U;
        ADC1->SMPR1 &= ~(0x7UL << shift);
        ADC1->SMPR1 |= 0x7UL << shift;
    }
}

void adc_init(void) {
    RCC->APB2ENR |= RCC_APB2ENR_ADC1EN | RCC_APB2ENR_IOPAEN;

    gpio_config_input(GPIOA, 5U, GPIO_CNF_ANALOG);

    ADC1->CR2 = ADC_CR2_ADON;
    delay_ms(2U);

    ADC1->CR2 |= ADC_CR2_RSTCAL;
    while ((ADC1->CR2 & ADC_CR2_RSTCAL) != 0U) {
    }

    ADC1->CR2 |= ADC_CR2_CAL;
    while ((ADC1->CR2 & ADC_CR2_CAL) != 0U) {
    }

    ADC1->CR2 |= ADC_CR2_ADON | ADC_CR2_TSVREFE;
    adc_set_sample_time(5U);
    adc_set_sample_time(16U);
}

uint16_t adc_read_channel(uint8_t channel) {
    adc_set_sample_time(channel);
    ADC1->SQR1 = 0U;
    ADC1->SQR2 = 0U;
    ADC1->SQR3 = channel;
    ADC1->CR2 |= ADC_CR2_EXTSEL_SWSTART | ADC_CR2_EXTTRIG;
    ADC1->SR = 0U;
    ADC1->CR2 |= ADC_CR2_SWSTART;

    while ((ADC1->SR & ADC_SR_EOC) == 0U) {
    }

    return (uint16_t) ADC1->DR;
}

uint16_t adc_read_battery_mv(void) {
    uint32_t raw = adc_read_channel(5U);
    uint32_t pin_mv = (raw * MCU_VREF_MV) / 4095UL;

    return (uint16_t) ((pin_mv * VBAT_DIVIDER_MILLI_RATIO) / 1000UL);
}

int16_t adc_read_mcu_temperature_centi(void) {
    uint32_t raw = adc_read_channel(16U);
    int32_t sensor_mv = (int32_t) ((raw * MCU_VREF_MV) / 4095UL);
    int32_t temp_centi = ((1430 - sensor_mv) * 1000) / 43 + 2500;

    return (int16_t) temp_centi;
}
