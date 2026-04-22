/*********************************************************************
This is a library for our Monochrome OLEDs based on SSD1306 drivers

  Pick one up today in the adafruit shop!
  ------> http://www.adafruit.com/category/63_98

These displays use SPI to communicate, 4 or 5 pins are required to  
interface

Adafruit invests time and resources providing this open source code, 
please support Adafruit and open-source hardware by purchasing 
products from Adafruit!

Written by Limor Fried/Ladyada  for Adafruit Industries.  
BSD license, check license.txt for more information
All text above, and the splash screen below must be included in any redistribution
*********************************************************************/

/*
 *  Modified by Neal Horman 7/14/2012 for use in mbed
 *  Modified by Jiri Stepanovsky 6/4/2018 for LPE compatibility
 */

#include "mbed.h"
#include "SSD1306_mini.h"

#define SSD1306_SETCONTRAST 0x81
#define SSD1306_DISPLAYALLON_RESUME 0xA4
#define SSD1306_DISPLAYALLON 0xA5
#define SSD1306_NORMALDISPLAY 0xA6
#define SSD1306_INVERTDISPLAY 0xA7
#define SSD1306_DISPLAYOFF 0xAE
#define SSD1306_DISPLAYON 0xAF
#define SSD1306_SETDISPLAYOFFSET 0xD3
#define SSD1306_SETCOMPINS 0xDA
#define SSD1306_SETVCOMDETECT 0xDB
#define SSD1306_SETDISPLAYCLOCKDIV 0xD5
#define SSD1306_SETPRECHARGE 0xD9
#define SSD1306_SETMULTIPLEX 0xA8
#define SSD1306_SETLOWCOLUMN 0x00
#define SSD1306_SETHIGHCOLUMN 0x10
#define SSD1306_SETSTARTLINE 0x40
#define SSD1306_MEMORYMODE 0x20
#define SSD1306_COMSCANINC 0xC0
#define SSD1306_COMSCANDEC 0xC8
#define SSD1306_SEGREMAP 0xA0
#define SSD1306_CHARGEPUMP 0x8D

void SSD1306_mini::begin(uint8_t vccstate)
{
    rst = 1;
    // VDD (3.3V) goes high at start, lets just chill for a ms
     thread_sleep_for(5);
    // bring reset low
    rst = 0;
    // wait 10ms
     thread_sleep_for(10);
    // bring out of reset
    rst = 1;
    // turn on VCC (9V?)

    command(SSD1306_DISPLAYOFF);
    command(SSD1306_SETDISPLAYCLOCKDIV);
    command(0x80);                                  // the suggested ratio 0x80

    command(SSD1306_SETMULTIPLEX);
    command(OLED_HEIGHT-1);

    command(SSD1306_SETDISPLAYOFFSET);
    command(0x0);                                   // no offset

    command(SSD1306_SETSTARTLINE | 0x0);            // line #0

    command(SSD1306_CHARGEPUMP);
    command((vccstate == SSD1306_EXTERNALVCC) ? 0x10 : 0x14);

    command(SSD1306_MEMORYMODE);
    command(0x00);                                  // 0x0 act like ks0108

    command(SSD1306_SEGREMAP | 0x1);

    command(SSD1306_COMSCANDEC);

    command(SSD1306_SETCOMPINS);
    command(OLED_HEIGHT == 32 ? 0x02 : 0x12);        // TODO - calculate based on _rawHieght ?

    command(SSD1306_SETCONTRAST);
    command(OLED_HEIGHT == 32 ? 0x8F : ((vccstate == SSD1306_EXTERNALVCC) ? 0x9F : 0xCF) );

    command(SSD1306_SETPRECHARGE);
    command((vccstate == SSD1306_EXTERNALVCC) ? 0x22 : 0xF1);

    command(SSD1306_SETVCOMDETECT);
    command(0x40);

    command(SSD1306_DISPLAYALLON_RESUME);

    command(SSD1306_NORMALDISPLAY);
    
    command(SSD1306_DISPLAYON);
}

// Set a single pixel
void SSD1306_mini::drawPixel(int16_t x, int16_t y, uint16_t color)
{
    if ((x < 0) || (x >= OLED_WIDTH) || (y < 0) || (y >= OLED_HEIGHT))
        return;
    // x is which column
    if (color == WHITE) 
        buffer[x+ (y/8)*OLED_WIDTH] |= 1<<(y%8);  
    else // else black
        buffer[x+ (y/8)*OLED_WIDTH] &= ~(1<<(y%8)); 
}

void SSD1306_mini::invertDisplay(bool i)
{
	command(i ? SSD1306_INVERTDISPLAY : SSD1306_NORMALDISPLAY);
}

// Send the display buffer out to the display
void SSD1306_mini::display(void)
{
	command(SSD1306_SETLOWCOLUMN | 0x0);  // low col = 0
	command(SSD1306_SETHIGHCOLUMN | 0x0);  // hi col = 0
	command(SSD1306_SETSTARTLINE | 0x0); // line #0
	sendDisplayBuffer();
}

// Clear the display buffer. Requires a display() call at some point afterwards
void SSD1306_mini::clearDisplay(void)
{
	for(uint16_t i=0, q=OLED_BUFFER_SIZE; i<q; i++)
		buffer[i] = 0;
}
