#ifndef STM32F100_H
#define STM32F100_H

#include <stdint.h>

typedef struct {
    volatile uint32_t CRL;
    volatile uint32_t CRH;
    volatile uint32_t IDR;
    volatile uint32_t ODR;
    volatile uint32_t BSRR;
    volatile uint32_t BRR;
    volatile uint32_t LCKR;
} GPIO_TypeDef;

typedef struct {
    volatile uint32_t EVCR;
    volatile uint32_t MAPR;
    volatile uint32_t EXTICR1;
    volatile uint32_t EXTICR2;
    volatile uint32_t EXTICR3;
    volatile uint32_t EXTICR4;
    volatile uint32_t MAPR2;
} AFIO_TypeDef;

typedef struct {
    volatile uint32_t CR;
    volatile uint32_t CFGR;
    volatile uint32_t CIR;
    volatile uint32_t APB2RSTR;
    volatile uint32_t APB1RSTR;
    volatile uint32_t AHBENR;
    volatile uint32_t APB2ENR;
    volatile uint32_t APB1ENR;
    volatile uint32_t BDCR;
    volatile uint32_t CSR;
    volatile uint32_t AHBRSTR;
    volatile uint32_t CFGR2;
} RCC_TypeDef;

typedef struct {
    volatile uint32_t SR;
    volatile uint32_t DR;
    volatile uint32_t BRR;
    volatile uint32_t CR1;
    volatile uint32_t CR2;
    volatile uint32_t CR3;
    volatile uint32_t GTPR;
} USART_TypeDef;

typedef struct {
    volatile uint32_t CR1;
    volatile uint32_t CR2;
    volatile uint32_t SR;
    volatile uint32_t DR;
    volatile uint32_t CRCPR;
    volatile uint32_t RXCRCR;
    volatile uint32_t TXCRCR;
    volatile uint32_t I2SCFGR;
    volatile uint32_t I2SPR;
} SPI_TypeDef;

typedef struct {
    volatile uint32_t CR1;
    volatile uint32_t CR2;
    volatile uint32_t SMCR;
    volatile uint32_t DIER;
    volatile uint32_t SR;
    volatile uint32_t EGR;
    volatile uint32_t CCMR1;
    volatile uint32_t CCMR2;
    volatile uint32_t CCER;
    volatile uint32_t CNT;
    volatile uint32_t PSC;
    volatile uint32_t ARR;
    volatile uint32_t RCR;
    volatile uint32_t CCR1;
    volatile uint32_t CCR2;
    volatile uint32_t CCR3;
    volatile uint32_t CCR4;
    volatile uint32_t BDTR;
    volatile uint32_t DCR;
    volatile uint32_t DMAR;
    volatile uint32_t OR;
} TIM_TypeDef;

typedef struct {
    volatile uint32_t SR;
    volatile uint32_t CR1;
    volatile uint32_t CR2;
    volatile uint32_t SMPR1;
    volatile uint32_t SMPR2;
    volatile uint32_t JOFR1;
    volatile uint32_t JOFR2;
    volatile uint32_t JOFR3;
    volatile uint32_t JOFR4;
    volatile uint32_t HTR;
    volatile uint32_t LTR;
    volatile uint32_t SQR1;
    volatile uint32_t SQR2;
    volatile uint32_t SQR3;
    volatile uint32_t JSQR;
    volatile uint32_t JDR1;
    volatile uint32_t JDR2;
    volatile uint32_t JDR3;
    volatile uint32_t JDR4;
    volatile uint32_t DR;
} ADC_TypeDef;

typedef struct {
    volatile uint32_t CTRL;
    volatile uint32_t LOAD;
    volatile uint32_t VAL;
    volatile uint32_t CALIB;
} SysTick_TypeDef;

#define PERIPH_BASE        0x40000000UL
#define APB2PERIPH_BASE    (PERIPH_BASE + 0x00010000UL)
#define AHBPERIPH_BASE     (PERIPH_BASE + 0x00020000UL)
#define GPIOA_BASE         (APB2PERIPH_BASE + 0x00000800UL)
#define GPIOB_BASE         (APB2PERIPH_BASE + 0x00000C00UL)
#define GPIOC_BASE         (APB2PERIPH_BASE + 0x00001000UL)
#define AFIO_BASE          (APB2PERIPH_BASE + 0x00000000UL)
#define TIM15_BASE         (APB2PERIPH_BASE + 0x00004000UL)
#define RCC_BASE           (AHBPERIPH_BASE + 0x00001000UL)
#define USART1_BASE        (APB2PERIPH_BASE + 0x00003800UL)
#define USART3_BASE        (PERIPH_BASE + 0x00004800UL)
#define SPI2_BASE          (PERIPH_BASE + 0x00003800UL)
#define ADC1_BASE          (APB2PERIPH_BASE + 0x00002400UL)
#define SYSTICK_BASE       0xE000E010UL

#define GPIOA              ((GPIO_TypeDef *) GPIOA_BASE)
#define GPIOB              ((GPIO_TypeDef *) GPIOB_BASE)
#define GPIOC              ((GPIO_TypeDef *) GPIOC_BASE)
#define AFIO               ((AFIO_TypeDef *) AFIO_BASE)
#define TIM15              ((TIM_TypeDef *) TIM15_BASE)
#define RCC                ((RCC_TypeDef *) RCC_BASE)
#define USART1             ((USART_TypeDef *) USART1_BASE)
#define USART3             ((USART_TypeDef *) USART3_BASE)
#define SPI2               ((SPI_TypeDef *) SPI2_BASE)
#define ADC1               ((ADC_TypeDef *) ADC1_BASE)
#define SYSTICK            ((SysTick_TypeDef *) SYSTICK_BASE)

#define RCC_APB2ENR_AFIOEN     (1U << 0)
#define RCC_APB2ENR_IOPAEN     (1U << 2)
#define RCC_APB2ENR_IOPBEN     (1U << 3)
#define RCC_APB2ENR_IOPCEN     (1U << 4)
#define RCC_APB2ENR_ADC1EN     (1U << 9)
#define RCC_APB2ENR_USART1EN   (1U << 14)
#define RCC_APB2ENR_TIM15EN    (1U << 16)

#define RCC_APB1ENR_SPI2EN     (1U << 14)
#define RCC_APB1ENR_USART3EN   (1U << 18)

#define AFIO_MAPR_SWJ_CFG_JTAGDISABLE (0x2U << 24)
#define AFIO_MAPR2_TIM15_REMAP       (1U << 0)

#define GPIO_MODE_INPUT            0x0U
#define GPIO_MODE_OUTPUT_10MHZ     0x1U
#define GPIO_MODE_OUTPUT_2MHZ      0x2U
#define GPIO_MODE_OUTPUT_50MHZ     0x3U
#define GPIO_CNF_ANALOG            0x0U
#define GPIO_CNF_FLOATING          0x1U
#define GPIO_CNF_INPUT_PUPD        0x2U
#define GPIO_CNF_GP_PUSHPULL       0x0U
#define GPIO_CNF_GP_OPENDRAIN      0x1U
#define GPIO_CNF_AF_PUSHPULL       0x2U
#define GPIO_CNF_AF_OPENDRAIN      0x3U

#define USART_SR_RXNE          (1U << 5)
#define USART_SR_TXE           (1U << 7)
#define USART_CR1_UE           (1U << 13)
#define USART_CR1_TE           (1U << 3)
#define USART_CR1_RE           (1U << 2)

#define SPI_CR1_CPHA           (1U << 0)
#define SPI_CR1_CPOL           (1U << 1)
#define SPI_CR1_MSTR           (1U << 2)
#define SPI_CR1_BR_DIV16       (0x3U << 3)
#define SPI_CR1_SPE            (1U << 6)
#define SPI_CR1_LSBFIRST       (1U << 7)
#define SPI_CR1_SSI            (1U << 8)
#define SPI_CR1_SSM            (1U << 9)
#define SPI_SR_RXNE            (1U << 0)
#define SPI_SR_TXE             (1U << 1)
#define SPI_SR_BSY             (1U << 7)

#define TIM_CR1_CEN            (1U << 0)
#define TIM_CR1_ARPE           (1U << 7)
#define TIM_EGR_UG             (1U << 0)
#define TIM_CCMR1_OC2FE        (1U << 10)
#define TIM_CCMR1_OC2M_0       (1U << 12)
#define TIM_CCMR1_OC2M_1       (1U << 13)
#define TIM_CCER_CC2E          (1U << 4)
#define TIM_BDTR_MOE           (1U << 15)

#define ADC_SR_EOC             (1U << 1)
#define ADC_CR2_ADON           (1U << 0)
#define ADC_CR2_CONT           (1U << 1)
#define ADC_CR2_CAL            (1U << 2)
#define ADC_CR2_RSTCAL         (1U << 3)
#define ADC_CR2_EXTSEL_SWSTART (0x7U << 17)
#define ADC_CR2_EXTTRIG        (1U << 20)
#define ADC_CR2_SWSTART        (1U << 22)
#define ADC_CR2_TSVREFE        (1U << 23)

#define SYSTICK_CTRL_ENABLE    (1U << 0)
#define SYSTICK_CTRL_TICKINT   (1U << 1)
#define SYSTICK_CTRL_CLKSRC    (1U << 2)
#define SYSTICK_CTRL_COUNTFLAG (1U << 16)

#endif
