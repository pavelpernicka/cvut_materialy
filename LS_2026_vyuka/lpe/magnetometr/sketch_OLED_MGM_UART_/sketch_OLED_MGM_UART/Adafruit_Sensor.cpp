#include "Adafruit_Sensor.h"

/**************************************************************************/
/*!
    @brief  Prints sensor information to serial console
*/
/**************************************************************************/
void Adafruit_Sensor::printSensorDetails(void) {
  sensor_t sensor;
  getSensor(&sensor);
  Serial2.println(F("------------------------------------"));
  Serial2.print(F("Sensor:       "));
  Serial2.println(sensor.name);
  Serial2.print(F("Type:         "));
 
}
