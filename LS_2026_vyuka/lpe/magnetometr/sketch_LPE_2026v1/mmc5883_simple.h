#ifndef MMC5883_SIMPLE_H
#define MMC5883_SIMPLE_H

#include <Arduino.h>
#include <Wire.h>

#ifdef __cplusplus
extern "C" {
#endif

/* I2C adresa senzoru MMC5883 */
#define MMC5883_I2C_ADDRESS 0x30

/* Registry použité v této jednoduché knihovně */
#define MMC5883_REG_OUT_X_L    0x00
#define MMC5883_REG_STATUS     0x07
#define MMC5883_REG_INTCTRL0   0x08
#define MMC5883_REG_INTCTRL1   0x09
#define MMC5883_REG_INTCTRL2   0x0A
#define MMC5883_REG_PRODUCT_ID 0x2F

/* Bity v registrech */
#define MMC5883_STATUS_MEAS_DONE 0x01
#define MMC5883_CTRL0_SET        0x08
#define MMC5883_CTRL0_RESET      0x10
#define MMC5883_CTRL1_SOFT_RESET 0x80
#define MMC5883_CTRL2_CMM_EN     0x01   /* continuous mode, 14 Hz v původní knihovně */
#define MMC5883_CTRL2_INT_MEAS   0x40

/* Přepočet z raw dat na nT podle původní knihovny */
#define MMC5883_NT_PER_LSB 24.41f

/* Jednoduchá datová struktura */
typedef struct
{
    TwoWire* wire;      /* který I2C port se použije, např. &Wire nebo &Wire1 */
    uint8_t address;    /* I2C adresa senzoru */
    uint16_t raw_x;
    uint16_t raw_y;
    uint16_t raw_z;
} mmc5883_t;

/* Inicializace struktury */
void mmc5883_init_struct(mmc5883_t* dev, TwoWire* wire, uint8_t address);

/* Inicializace senzoru. Vrací true při úspěchu. */
bool mmc5883_begin(mmc5883_t* dev);

/* Soft reset senzoru */
void mmc5883_soft_reset(mmc5883_t* dev);

/* SET a RESET flip pulzy */
void mmc5883_set_flip(mmc5883_t* dev);
void mmc5883_reset_flip(mmc5883_t* dev);

/* Čtení posledních raw dat */
bool mmc5883_read_raw(mmc5883_t* dev, int32_t* x, int32_t* y, int32_t* z);

/* Čtení dat přímo v nT */
bool mmc5883_read_nT(mmc5883_t* dev, float* x_nT, float* y_nT, float* z_nT);

#ifdef __cplusplus
}
#endif

#endif
