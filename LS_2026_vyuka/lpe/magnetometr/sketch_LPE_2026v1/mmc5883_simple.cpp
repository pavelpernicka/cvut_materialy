#include "mmc5883_simple.h"

/* -------------------------------------------------------
   Pomocné interní funkce
   ------------------------------------------------------- */
static bool mmc5883_write_reg(mmc5883_t* dev, uint8_t reg, uint8_t value)
{
    dev->wire->beginTransmission(dev->address);
    dev->wire->write(reg);
    dev->wire->write(value);
    return (dev->wire->endTransmission() == 0);
}

static bool mmc5883_read_reg(mmc5883_t* dev, uint8_t reg, uint8_t* value)
{
    dev->wire->beginTransmission(dev->address);
    dev->wire->write(reg);
    if (dev->wire->endTransmission(false) != 0) {
        return false;
    }

    if (dev->wire->requestFrom((int)dev->address, 1) != 1) {
        return false;
    }

    *value = dev->wire->read();
    return true;
}

static bool mmc5883_read_regs(mmc5883_t* dev, uint8_t first_reg, uint8_t* buffer, uint8_t length)
{
    dev->wire->beginTransmission(dev->address);
    dev->wire->write(first_reg);
    if (dev->wire->endTransmission(false) != 0) {
        return false;
    }

    if (dev->wire->requestFrom((int)dev->address, (int)length) != length) {
        return false;
    }

    for (uint8_t i = 0; i < length; i++) {
        buffer[i] = dev->wire->read();
    }

    return true;
}

/* -------------------------------------------------------
   Veřejné funkce
   ------------------------------------------------------- */
void mmc5883_init_struct(mmc5883_t* dev, TwoWire* wire, uint8_t address)
{
    dev->wire = wire;
    dev->address = address;
    dev->raw_x = 0;
    dev->raw_y = 0;
    dev->raw_z = 0;
}

bool mmc5883_begin(mmc5883_t* dev)
{
    uint8_t id = 0;

    if (dev == NULL || dev->wire == NULL) {
        return false;
    }

    dev->wire->begin();
    delay(10);

    if (!mmc5883_read_reg(dev, MMC5883_REG_PRODUCT_ID, &id)) {
        return false;
    }

    /* V přiložené Adafruit knihovně se kontroluje hodnota 0x0C. */
    if (id != 0x0C) {
        return false;
    }

    mmc5883_soft_reset(dev);

    /* Nastavení jako v původní knihovně:
       - continuous mode 14 Hz
       - povolit measurement done interrupt bit
    */
    if (!mmc5883_write_reg(dev, MMC5883_REG_INTCTRL2, MMC5883_CTRL2_CMM_EN | MMC5883_CTRL2_INT_MEAS)) {
        return false;
    }

    /* Pro jistotu po startu pošleme SET pulz */
    mmc5883_set_flip(dev);

    return true;
}

void mmc5883_soft_reset(mmc5883_t* dev)
{
    mmc5883_write_reg(dev, MMC5883_REG_INTCTRL1, MMC5883_CTRL1_SOFT_RESET);
    delay(10);
    mmc5883_write_reg(dev, MMC5883_REG_INTCTRL1, 0x00);
}

void mmc5883_set_flip(mmc5883_t* dev)
{
    mmc5883_write_reg(dev, MMC5883_REG_INTCTRL0, MMC5883_CTRL0_SET);
}

void mmc5883_reset_flip(mmc5883_t* dev)
{
    mmc5883_write_reg(dev, MMC5883_REG_INTCTRL0, MMC5883_CTRL0_RESET);
}

bool mmc5883_read_raw(mmc5883_t* dev, int32_t* x, int32_t* y, int32_t* z)
{
    uint8_t status = 0;
    uint8_t data[6];
    uint32_t timeout_start = millis();

    /* Čekání na nové měření */
    while (1) {
        if (!mmc5883_read_reg(dev, MMC5883_REG_STATUS, &status)) {
            return false;
        }

        if ((status & MMC5883_STATUS_MEAS_DONE) != 0) {
            break;
        }

        if ((millis() - timeout_start) > 100) {
            return false;
        }

        delay(1);
    }

    if (!mmc5883_read_regs(dev, MMC5883_REG_OUT_X_L, data, 6)) {
        return false;
    }

    dev->raw_x = (uint16_t)data[0] | ((uint16_t)data[1] << 8);
    dev->raw_y = (uint16_t)data[2] | ((uint16_t)data[3] << 8);
    dev->raw_z = (uint16_t)data[4] | ((uint16_t)data[5] << 8);

    /* Podle původní knihovny je nulový bod 32768 */
    if (x != NULL) *x = (int32_t)dev->raw_x - 32768;
    if (y != NULL) *y = (int32_t)dev->raw_y - 32768;
    if (z != NULL) *z = (int32_t)dev->raw_z - 32768;

    /* Smazání measurement done flagu zápisem 1 do bitu 0 */
    mmc5883_write_reg(dev, MMC5883_REG_STATUS, MMC5883_STATUS_MEAS_DONE);

    return true;
}

bool mmc5883_read_nT(mmc5883_t* dev, float* x_nT, float* y_nT, float* z_nT)
{
    int32_t x;
    int32_t y;
    int32_t z;

    if (!mmc5883_read_raw(dev, &x, &y, &z)) {
        return false;
    }

    if (x_nT != NULL) *x_nT = x * MMC5883_NT_PER_LSB;
    if (y_nT != NULL) *y_nT = y * MMC5883_NT_PER_LSB;
    if (z_nT != NULL) *z_nT = z * MMC5883_NT_PER_LSB;

    return true;
}
