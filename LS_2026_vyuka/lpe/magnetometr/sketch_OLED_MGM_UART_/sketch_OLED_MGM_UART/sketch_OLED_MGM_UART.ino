#include <SPI.h>
#include "SSD1306Ascii.h"
#include "SSD1306AsciiSpi.h"
#include <Adafruit_MMC5883.h>
#include <pinmap.h> 
#include <string.h> 

// pin definitions
#define CS_PIN  PA4
#define RST_PIN PB0
#define DC_PIN  PA8 //BEWARE - CHANGE with respect to KEILstudio code
SSD1306AsciiSpi oled;
const int analogip = PA0; //Initialize the analog input pin
HardwareSerial Serial2(PA_3_ALT1, PA_2_ALT1); // UART2 TX RX
TwoWire Wire1(PA14, PA13);
Adafruit_MMC5883 mag = Adafruit_MMC5883(1);
sensors_event_t event;
sensors_event_t event1;
//------------------------------------------------------------------------------
void setup() {
  Serial2.begin(115200); 
  Serial.begin(115200); 
  analogReadResolution(12);
  oled.begin(&Adafruit128x64, CS_PIN, DC_PIN, RST_PIN);
  oled.setFont(Adafruit5x7);  
  oled.clear();  
  Wire1.setClock(50000);
  if(!mag.begin(MMC5883_ADDRESS_MAG,&Wire1)){
    /* There was a problem detecting the MMC5883 ... check your connections */
    Serial2.println("MGM error!");
    while(1);
  }
}
uint8_t i=1;
//------------------------------------------------------------------------------
void loop() {
  Serial.println(i++);
  Serial2.println(i);
  int val = analogRead(PA0);    // read the ADC value from pin A7
  float voltage = (float(val)/4096) * 3.3; //formulae to convert the ADC value to voltage
  Serial2.println(val);
  delay(500);
  oled.clear();  
  oled.set1X();
  oled.println("Hello world!");
  oled.println();
  oled.set2X();
  oled.println("LPE2024");
  char buf[25];
  dtostrf(voltage,4,2, buf);
  oled.println(buf);
  oled.invertDisplay(0);
  delay(500);
  oled.invertDisplay(1);
  mag.resetFlip();
  delay(50);
  mag.getEvent(&event);
  /* Display the results (magnetic vector values are in nano-Tesla (nT)) */
  Serial2.print("Xr: "); Serial2.print(event.magnetic.x); Serial2.print("  ");
  Serial2.print("Yr: "); Serial2.print(event.magnetic.y); Serial2.print("  ");
  Serial2.print("Zr: "); Serial2.print(event.magnetic.z); Serial2.print("  ");Serial2.println("nT");
  mag.setFlip();
  delay(50);
  mag.getEvent(&event1);
  /* Display the results (magnetic vector values are in nano-Tesla (nT)) */
  Serial2.print("Xs: "); Serial2.print(event1.magnetic.x); Serial2.print("  ");
  Serial2.print("Ys: "); Serial2.print(event1.magnetic.y); Serial2.print("  ");
  Serial2.print("Zs: "); Serial2.print(event1.magnetic.z); Serial2.print("  ");Serial2.println("nT");
}