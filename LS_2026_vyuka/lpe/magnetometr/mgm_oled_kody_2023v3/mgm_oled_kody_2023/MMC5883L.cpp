#include "MMC5883L.h"
#include <new>

MMC5883L::MMC5883L(PinName sda, PinName scl) : i2c_(*reinterpret_cast<I2C*>(i2cRaw))
{
    // Placement new to avoid additional heap memory allocation.
    new(i2cRaw) I2C(sda, scl);

    init();
}

MMC5883L::~MMC5883L()
{
    // If the I2C object is initialized in the buffer in this object, call destructor of it.
    if(&i2c_ == reinterpret_cast<I2C*>(&i2cRaw))
        reinterpret_cast<I2C*>(&i2cRaw)->~I2C();
}

void MMC5883L::init()
{
    setConfiguration0(FLIP_SET);        // restore sensitivity by flip pulse
    setConfiguration1(DATARATE_100);    // smallest rate
    setConfiguration2(OUTPUT_RATE_OFF); // single mode
     thread_sleep_for(10);
}

void MMC5883L::setConfiguration0(char config)
{
    char cmd[2];
    cmd[0] = INTERNAL_CONTROL_0; // register a address
    cmd[1] = config;             // register data

    i2c_.write(I2C_ADDRESS, cmd, 2);
}

void MMC5883L::startMeasurement_mag()
{
    char cmd[2];
    cmd[0] = INTERNAL_CONTROL_0; // register a address
    cmd[1] = MAGNETIC_MEASUREMENT_START; // register data

    i2c_.write(I2C_ADDRESS, cmd, 2);
}

void MMC5883L::flipSet()
{
    char cmd[2];
    cmd[0] = INTERNAL_CONTROL_0; // register a address
    cmd[1] = FLIP_SET;          // register data

    i2c_.write(I2C_ADDRESS, cmd, 2);
}
void MMC5883L::flipReset()
{
    char cmd[2];
    cmd[0] = INTERNAL_CONTROL_0; // register a address
    cmd[1] = FLIP_RESET;         // register data

    i2c_.write(I2C_ADDRESS, cmd, 2);
}

void MMC5883L::startMeasurement_temp()
{
    char cmd[2];
    cmd[0] = INTERNAL_CONTROL_0; // register a address
    cmd[1] = TEMP_MEASUREMENT_START; // register data

    i2c_.write(I2C_ADDRESS, cmd, 2);
}

void MMC5883L::setConfiguration1(char config)
{
    char cmd[2];
    cmd[0] = INTERNAL_CONTROL_1; // register b address
    cmd[1] = config;            // register data

    i2c_.write(I2C_ADDRESS, cmd, 2);
}

void MMC5883L::setConfiguration2(char config)
{
    char cmd[2];
    cmd[0] = INTERNAL_CONTROL_2; // register b address
    cmd[1] = config;            // register data

    i2c_.write(I2C_ADDRESS, cmd, 2);
}

char MMC5883L::getConfiguration0()
{
    char cmd[2];
    cmd[0] = INTERNAL_CONTROL_0; // register address
    i2c_.write(I2C_ADDRESS, cmd, 1, true);
    i2c_.read(I2C_ADDRESS, &cmd[1], 1, false);
    return cmd[1];
}

char MMC5883L::getConfiguration1()
{
    char cmd[2];
    cmd[0] = INTERNAL_CONTROL_1; // register address
    i2c_.write(I2C_ADDRESS, cmd, 1, true);
    i2c_.read(I2C_ADDRESS, &cmd[1], 1, false);
    return cmd[1];
}


char MMC5883L::getConfiguration2()
{
    char cmd[2];
    cmd[0] = INTERNAL_CONTROL_2; // register address
    i2c_.write(I2C_ADDRESS, cmd, 1, true);
    i2c_.read(I2C_ADDRESS, &cmd[1], 1, false);
    return cmd[1];
}

char MMC5883L::getStatus()
{
    char cmd[2];
    cmd[0] = STATUS_REG; // status register
    i2c_.write(I2C_ADDRESS, cmd, 1, true);
    i2c_.read(I2C_ADDRESS, &cmd[1], 1, false);
    return cmd[1];
}

void MMC5883L::getXYZ_RAW(int16_t output[3])
{
    char cmd[2];
    char data[6];

    startMeasurement_mag(); // start measurement
    while((getStatus()&STATUS_M_DONE)==0); // wait until complete

    cmd[0] = OUTPUT_REG; // starting addr for reading
    i2c_.write(I2C_ADDRESS, cmd, 1, true);
    i2c_.read(I2C_ADDRESS, data, 6, false);
    int32_t tmp[3];
    for(int i = 0; i < 3; i++) { // fill the output variables, X, Y, Z, LSB first
        tmp[i] = ((uint16_t)(data[i*2+1] << 8)) | (uint16_t)(data[i*2]);
        tmp[i] -= 65536/2;
        output[i] = tmp[i];
    }
}

void MMC5883L::getXYZ_nT(int32_t output[3])
{
    int16_t data[3];
    getXYZ_RAW(data);

    for(int i = 0; i < 3; i++) {
        int64_t tmp =  data[i];
        tmp *= 800000;
        tmp /= (65536/2); // +- 8G = 16G FS
        output[i] = tmp;
    }
}

void MMC5883L::getXYZ_OffsetRemoved_RAW(int16_t output[3])
{
    // TODO: offset reemove
    int16_t dataR[3];
    int16_t dataS[3];
    int32_t outTemp[3];
    ?
    thread_sleep_for(5);
    getXYZ_RAW(dataS);
    ?
    thread_sleep_for(5);
    getXYZ_RAW(dataR);
    
    for(int i = 0; i < 3; i++) {
    ?   
    }
}

void MMC5883L::getXYZ_OffsetRemoved_nT(int32_t output[3])
{
    int16_t data[3];
    getXYZ_OffsetRemoved_RAW(data);

    for(int i = 0; i < 3; i++) {
        int64_t tmp =  data[i];
        tmp *= 800000;
        tmp /= (65536/2); // +- 8G = 16G FS
        output[i] = tmp;
    }
}


double MMC5883L::getHeadingXY()
{
    int16_t raw_data[3];
    getXYZ_OffsetRemoved_RAW(raw_data);

    double heading = atan2(static_cast<double>(raw_data[0]), static_cast<double>(raw_data[1])); // heading = arctan(X/Y)

    heading += DECLINATION_ANGLE;

    if(heading < 0.0) // fix sign
        heading += PI2;

    if(heading > PI2) // fix overflow
        heading -= PI2;
    return heading;
}
double MMC5883L::getHeadingXY(int16_t output[3])
{
    getXYZ_OffsetRemoved_RAW(output);

    double heading = atan2(static_cast<double>(output[0]), static_cast<double>(output[1])); // heading = arctan(X/Y)

    heading += DECLINATION_ANGLE;

    if(heading < 0.0) // fix sign
        heading += PI2;

    if(heading > PI2) // fix overflow
        heading -= PI2;
    return heading;
}
double MMC5883L::getHeadingXY(int32_t output[3])
{
    getXYZ_OffsetRemoved_nT(output);

    double heading = atan2(static_cast<double>(output[0]), static_cast<double>(output[1])); // heading = arctan(X/Y)

    heading += DECLINATION_ANGLE;

    if(heading < 0.0) // fix sign
        heading += PI2;

    if(heading > PI2) // fix overflow
        heading -= PI2;
    return heading;
}

double MMC5883L::getHeadingXYDeg()
{
    return (getHeadingXY() * RAD_TO_DEG);
}
double MMC5883L::getHeadingXYDeg_RAW(int16_t output[3])
{
    return (getHeadingXY(output) * RAD_TO_DEG);
}
double MMC5883L::getHeadingXYDeg_nT(int32_t output[3])
{
    return (getHeadingXY(output) * RAD_TO_DEG);
}

