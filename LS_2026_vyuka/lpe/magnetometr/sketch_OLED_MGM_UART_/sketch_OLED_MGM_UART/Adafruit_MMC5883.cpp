/*!
 * @file Adafruit_MMC5883.cpp
 *
 * @mainpage Adafruit MMC5883 Unified Library
 *
 * @section intro_sec Introduction
 *
 * This is a library for the MMC5883 magnentometer/compass
 *
 * Designed specifically to work with the Adafruit MMC5883 Breakout
 * http://www.adafruit.com/products/1746
 *
 * These displays use I2C to communicate, 2 pins are required to interface.
 *
 * Adafruit invests time and resources providing this open source code,
 * please support Adafruit andopen-source hardware by purchasing products
 * from Adafruit!
 *
 * @section author Author
 *
 * Written by ladyada for Adafruit Industries.
 *
 * @section license License
 *
 * BSD license, all text above must be included in any redistribution
 */

#include "Arduino.h"
#include <Wire.h>
#include <limits.h>

#include "Adafruit_MMC5883.h"

static float _mmc5883_nT_LSB = 24.41; // scale factor for converting to nT

/***************************************************************************
 MAGNETOMETER
 ***************************************************************************/

/***************************************************************************
 CONSTRUCTOR
 ***************************************************************************/

/**************************************************************************/
/*!
    @brief  Instantiates a new Adafruit_MMC5883 class
    @param sensorID sensor ID, -1 by default
*/
/**************************************************************************/
Adafruit_MMC5883::Adafruit_MMC5883(int32_t sensorID) { _sensorID = sensorID; }

/***************************************************************************
 PUBLIC FUNCTIONS
 ***************************************************************************/

/**************************************************************************/
/*!
    @brief  Setups the HW
    @param i2c_addr Device address
    @param theWire I2C interface object
    @return true on success
*/
/**************************************************************************/
bool Adafruit_MMC5883::begin(uint8_t i2c_addr, TwoWire *theWire) {
  if (!i2c_dev) {
    i2c_dev = new Adafruit_I2CDevice(MMC5883_ADDRESS_MAG, theWire);
  }
  // Enable I2C

  if (!i2c_dev->begin()) {
    return false;
  }

  Adafruit_BusIO_Register id_reg =
      Adafruit_BusIO_Register(i2c_dev, MMC5883_REGISTER_PRODID);
  if (id_reg.read() != 0x0C) {
    return false;
  }

  if (ctrl0_reg)
    delete ctrl0_reg;
  if (ctrl1_reg)
    delete ctrl1_reg;
  if (ctrl2_reg)
    delete ctrl2_reg;

  ctrl0_reg = new Adafruit_BusIO_Register(i2c_dev, MMC5883_REGISTER_INTCTRL0);
  ctrl1_reg = new Adafruit_BusIO_Register(i2c_dev, MMC5883_REGISTER_INTCTRL1);
  ctrl2_reg = new Adafruit_BusIO_Register(i2c_dev, MMC5883_REGISTER_INTCTRL2);

  reset();

  // set for continuous reads
  setContinuousFreq(MMC5883_CMFREQ_14HZ);
  // turn on DRDY interrupt
  setInterrupt(false, true);
  setFlip();

  return true;
}

/**************************************************************************/
/*!
    @brief  Reset device
*/
/**************************************************************************/
void Adafruit_MMC5883::reset(void) {
  ctrl1_reg->write(0x80 | ctrl1_reg->readCached());

  delay(10);

  ctrl1_reg->write(ctrl1_reg->readCached() & ~0x80);
}

/**************************************************************************/
/*!
    @brief  Set Interrupt
    @param motion motion
    @param meas measure

*/
/**************************************************************************/
void Adafruit_MMC5883::setInterrupt(bool motion, bool meas) {
  uint8_t c2 = ctrl2_reg->readCached();
  if (motion) {
    c2 |= 0x20;
  }
  if (meas) {
    c2 |= 0x40;
  }
  ctrl2_reg->write(c2);
}

/**************************************************************************/
/*!
    @brief  Sets the magnetometer's continuous or not data rate
    @param freq Frequency
*/
/**************************************************************************/
void Adafruit_MMC5883::setContinuousFreq(mmc5883CMFreq freq) {
  ctrl2_reg->write((uint8_t)freq | ctrl2_reg->readCached());
}

/**************************************************************************/
/*!
    @brief  Sets the magnetometer's SET flip pulse
    @param none
*/
/**************************************************************************/
void Adafruit_MMC5883::setFlip(void) {
  //ctrl0_reg->write(0x08 | ctrl0_reg->readCached());
  ctrl0_reg->write(0x08);
}

/**************************************************************************/
/*!
    @brief  Sets the magnetometer's RESET flip pulse
    @param none
*/
/**************************************************************************/
void Adafruit_MMC5883::resetFlip(void) {
  //ctrl0_reg->write(0x10 | ctrl0_reg->readCached());
  ctrl0_reg->write(0x10);
}


/**************************************************************************/
/*!
    @brief  Gets the most recent sensor event
    @param event Sensor event
    @return true on success
*/
/**************************************************************************/
bool Adafruit_MMC5883::getEvent(sensors_event_t *event) {
  /* Clear the event */
  memset(event, 0, sizeof(sensors_event_t));

  /* Read new data */
  read();

  event->version = sizeof(sensors_event_t);
  event->sensor_id = _sensorID;
  event->type = SENSOR_TYPE_MAGNETIC_FIELD;
  event->timestamp = 0;
  event->magnetic.x = (mag_x - 32768) * _mmc5883_nT_LSB;
  event->magnetic.y = (mag_y - 32768) * _mmc5883_nT_LSB;
  event->magnetic.z = (mag_z - 32768) * _mmc5883_nT_LSB;

  return true;
}

/**************************************************************************/
/*!
    @brief  Gets the sensor_t data
*/
/**************************************************************************/
void Adafruit_MMC5883::getSensor(sensor_t *sensor) {
  /* Clear the sensor_t object */
  memset(sensor, 0, sizeof(sensor_t));

  /* Insert the sensor name in the fixed length char array */
  strncpy(sensor->name, "MMC5883", sizeof(sensor->name) - 1);
  sensor->name[sizeof(sensor->name) - 1] = 0;
  sensor->version = 1;
  sensor->sensor_id = _sensorID;
  sensor->type = SENSOR_TYPE_MAGNETIC_FIELD;
  sensor->min_delay = 0;
  sensor->max_value = 800000;    // 8 gauss == 800 microTesla
  sensor->min_value = -800000;   // -8 gauss == -800 microTesla
  sensor->resolution = 24.41; // nT - Earth's magnetic field is 48900 nT in Prague
}

/**************************************************************************/
/*!
    @brief  Reads the raw data from the sensor
    @return true on success
*/
/**************************************************************************/
bool Adafruit_MMC5883::read() {
  uint8_t buffer[6];

  Adafruit_BusIO_Register status_reg =
      Adafruit_BusIO_Register(i2c_dev, MMC5883_REGISTER_STATUS);
  Adafruit_BusIO_RegisterBits meas_m_done =
      Adafruit_BusIO_RegisterBits(&status_reg, 1, 0);

  while (!meas_m_done.read()) {
    delay(1);
  }

  // Read the magnetometer
  buffer[0] = MMC5883_REGISTER_OUT_X_L;
  if (!i2c_dev->write_then_read(buffer, 1, buffer, 6)) {
    return false;
  }

  // Shift values to create properly formed integer (low byte first)
  mag_x = (uint16_t)buffer[0] | (uint16_t)buffer[1] << 8;
  mag_y = (uint16_t)buffer[2] | (uint16_t)buffer[3] << 8;
  mag_z = (uint16_t)buffer[4] | (uint16_t)buffer[5] << 8;

  // clear IRQ
  meas_m_done.write(true);
  return true;
}
