#ifndef MMC5883L_H
#define MMC5883L_H

#include "mbed.h"

/*
* Defines
*/

//-----------
// Registers
//-----------
#define INTERNAL_CONTROL_0    0x08
#define INTERNAL_CONTROL_1    0x09
#define INTERNAL_CONTROL_2    0x0A
#define OUTPUT_REG      0x00
#define STATUS_REG      0x07

#define OUTPUT_RATE_OFF    0x00
#define OUTPUT_RATE_14     0x01
#define OUTPUT_RATE_5      0x02
#define OUTPUT_RATE_2_2    0x03
#define OUTPUT_RATE_1      0x04
#define OUTPUT_RATE_0_5    0x05
#define OUTPUT_RATE_0_25   0x06
#define OUTPUT_RATE_0_12   0x07
#define OUTPUT_RATE_0_06   0x08
#define OUTPUT_RATE_0_03   0x09
#define OUTPUT_RATE_0_015  0x0A
#define DRDY_INTERRUPT_EN    0x40
#define MOTION_INTERRUPT_EN  0x20

#define SW_RST  0x80
#define Z_INHIBIT       0x40
#define Y_INHIBIT       0x20
#define X_INHIBIT       0x10
#define DATARATE_100       0x00
#define DATARATE_200       0x01
#define DATARATE_400       0x02
#define DATARATE_600       0x03

#define MAGNETIC_MEASUREMENT_START 0x01
#define TEMP_MEASUREMENT_START 0x02
#define MOTION_DETECT_START 0x04
#define FLIP_SET 0x08
#define FLIP_RESET 0x10


// status register
#define STATUS_M_DONE       0x01
#define STATUS_T_DONE       0x02
#define STATUS_MOTION_DET   0x04

// Utility
#ifndef M_PI
#define M_PI 3.1415926535897932384626433832795
#endif

#define PI2         (2*M_PI)
#define RAD_TO_DEG  (180.0/M_PI)
#define DEG_TO_RAD  (M_PI/180.0)

// Once you have your heading, you must then add your 'Declination Angle', 
// which is  the 'Error' of the magnetic field in your location.
// Find yours here: http://www.magnetic-declination.com/
// Mine is:  -1° 13' WEST which is -1.2167 Degrees, or (which we need) 
// 0,021234839232597676519238237683278  radians, I will use 0.02123
// If you cannot find your Declination, put 0, your compass will be slightly off.

#define  DECLINATION_ANGLE -0.02123
//#define  DECLINATION_ANGLE 0


/**
 * The MMC5883L 3-Axis Digital Compass IC
 */
class MMC5883L
{

public:

    /**
     * The I2C address that can be passed directly to i2c object (it's already shifted 1 bit left).
     */
    static const int I2C_ADDRESS = 0x60;

    /**
     * Constructor.
     *
     * Calls init function
     *
     * @param sda - mbed pin to use for the SDA I2C line.
     * @param scl - mbed pin to use for the SCL I2C line.
     */
    MMC5883L(PinName sda, PinName scl);

    /**
    * Constructor that accepts external i2c interface object.
    * 
    * Calls init function
    *
    * @param i2c The I2C interface object to use.
    */
    MMC5883L(I2C &i2c) : i2c_(i2c) {
        init();
    }

    ~MMC5883L();

    void init();

    void setConfiguration0(char);
    void setConfiguration1(char);
    void setConfiguration2(char);

    char getConfiguration0();
    char getConfiguration1();
    char getConfiguration2();

    void flipSet();
    void flipReset();

    void startMeasurement_temp();
    void startMeasurement_mag();

    void getXYZ_RAW(int16_t raw[3]);
    void getXYZ_OffsetRemoved_RAW(int16_t raw[3]);
    void getXYZ_nT(int32_t raw[3]);
    void getXYZ_OffsetRemoved_nT(int32_t raw[3]);

    
    char getStatus();
    
    double getHeadingXY();
    double getHeadingXY(int16_t output[3]);    
    double getHeadingXY(int32_t output[3]);   
    double getHeadingXYDeg();
    double getHeadingXYDeg_RAW(int16_t output[3]);
    double getHeadingXYDeg_nT(int32_t output[3]);

private:

    I2C &i2c_;

    /**
     * The raw buffer for allocating I2C object in its own without heap memory.
     */
    char i2cRaw[sizeof(I2C)];
};

#endif // MMC5883L
