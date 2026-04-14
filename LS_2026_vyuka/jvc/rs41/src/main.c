#include "adc.h"
#include "board.h"
#include "gps.h"
#include "platform.h"
#include "protocol.h"
#include "si4032.h"
#include "spi.h"
#include "uart.h"

_Static_assert((RF_EST_TX_AIRTIME_MS * 100U) <= (TELEMETRY_INTERVAL_MS * CZ_433_MAX_DUTY_PERCENT),
               "Telemetry interval exceeds configured Czech 433 MHz duty-cycle budget.");

static void startup_blink(void) {
    for (uint8_t i = 0U; i < 3U; ++i) {
        platform_led_red(true);
        platform_led_green(false);
        delay_ms(80U);
        platform_led_red(false);
        platform_led_green(true);
        delay_ms(80U);
    }

    platform_led_red(false);
    platform_led_green(false);
}

int main(void) {
    uint8_t packet[TELEMETRY_PACKET_BYTES];
    uint32_t last_tx;

    platform_init();
    adc_init();
    uart1_init(GPS_BAUDRATE);
    spi2_init();
    gps_init();
    si4032_init();
    startup_blink();
    last_tx = platform_millis() - TELEMETRY_INTERVAL_MS;

    for (;;) {
        gps_poll();

        if ((platform_millis() - last_tx) >= TELEMETRY_INTERVAL_MS) {
            const gps_fix_t *fix = gps_get_fix();
            size_t packet_length;

            last_tx = platform_millis();
            packet_length = protocol_build_packet(packet,
                                                  platform_millis(),
                                                  fix,
                                                  adc_read_battery_mv(),
                                                  adc_read_mcu_temperature_centi());

            platform_led_green(true);
            si4032_transmit_packet(packet, packet_length);
            platform_led_green(false);
        }
    }
}
