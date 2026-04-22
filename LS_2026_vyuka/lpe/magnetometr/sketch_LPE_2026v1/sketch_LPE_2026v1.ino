#include <SPI.h>
#include "SSD1306Ascii.h"
#include "SSD1306AsciiSpi.h"
#include "mmc5883_simple.h"
#include <pinmap.h>

//nainstalovat v Arduino knihovnu: SSD1306Ascii  (přes library manager)

#define CS_PIN  PA4
#define RST_PIN PB0
#define DC_PIN  PA8

SSD1306AsciiSpi oled;
HardwareSerial Serial2(PA_3_ALT1, PA_2_ALT1);
TwoWire Wire1(PA14, PA13);

mmc5883_t mag;

void setup(){

    Serial2.begin(115200);

    oled.begin(&Adafruit128x64, CS_PIN, DC_PIN, RST_PIN);
    oled.setFont(Adafruit5x7);
    oled.clear();

    Wire1.setClock(50000);
    mmc5883_init_struct(&mag, &Wire1, MMC5883_I2C_ADDRESS);

    if (!mmc5883_begin(&mag)) {
        Serial2.println("MMC5883 chyba!");
        oled.println("MMC5883 chyba!");
        while (1) {
            delay(1000);
        }
    }

    Serial2.println("MMC5883 OK");
}

void loop()
{
    float xr, yr, zr;
    float xs, ys, zs;

    /* Měření po RESET flip */
    mmc5883_reset_flip(&mag);
    delay(500);
    if (mmc5883_read_nT(&mag, &xr, &yr, &zr)) {
        Serial2.print("Xr: "); Serial2.print(xr);
        Serial2.print("  Yr: "); Serial2.print(yr);
        Serial2.print("  Zr: "); Serial2.println(zr);
    }

    /* Měření po SET flip */
    mmc5883_set_flip(&mag);
    delay(500);
    if (mmc5883_read_nT(&mag, &xs, &ys, &zs)) {
        Serial2.print("Xs: "); Serial2.print(xs);
        Serial2.print("  Ys: "); Serial2.print(ys);
        Serial2.print("  Zs: "); Serial2.println(zs);
    }

    oled.clear();
    oled.println("MMC5883");
    oled.print("X: "); oled.println(xs, 0);
    oled.print("Y: "); oled.println(ys, 0);
    oled.print("Z: "); oled.println(zs, 0);

    delay(500);
}
