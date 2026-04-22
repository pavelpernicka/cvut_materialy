/* mbed Microcontroller Library
 * Copyright (c) 2019 ARM Limited
 * SPDX-License-Identifier: Apache-2.0
 */

#include "mbed.h"
#include "MMC5883L.h"
#include "SSD1306_mini.h"
#include <cstdint>

#define WAIT_TIME_MS 500 
DigitalOut led1(PA_8);

MMC5883L compass(PA_14, PA_13);
static BufferedSerial pc(PA_2, PA_3, 115200); // UART2 TX RX 9600 baud rate

SSD1306_mini_swspi gOled1(PA_5, PA_7,PA_6,PB_0,PA_4);
// SSD1306_mini_swspi(PinName D0, PinName D1, PinName DC, PinName RST, PinName CS)

void OLEDprintf(char *c){
    char *s;
    while(*c!=0x00){
        gOled1.writeChar(*c);
        c++;
    }
}


int main()
{
    char buffer[20];
    char comIN;
    unsigned char status = 0;
    int32_t data[3] = {0,0,0};
    unsigned int ccounter = 0;
    compass.init();

    gOled1.clearDisplay();
    gOled1.setTextCursor(10, 3);
    OLEDprintf("LPE");
    gOled1.display();
    gOled1.setTextSize(2);

    while (true)
    {
        led1 = !led1;
        ccounter +=1;
        if(ccounter>65000){ccounter =0;}
        double heading = compass.getHeadingXY(data);
        double Btot = sqrt(pow((double)data[0],2) + pow((double)data[1],2) + pow((double)data[2],2));
        printf("%+06d,%+06d,%+06d,%06u\r\n",data[0],data[1],data[2],(uint32_t)round(Btot));
        sprintf(buffer,"%05u",ccounter);
        gOled1.setTextCursor(10, 50);
        OLEDprintf(buffer);
        gOled1.display();
        thread_sleep_for(WAIT_TIME_MS);
        gOled1.invertDisplay(0);
        thread_sleep_for(WAIT_TIME_MS);
        gOled1.invertDisplay(1);
    }
}
