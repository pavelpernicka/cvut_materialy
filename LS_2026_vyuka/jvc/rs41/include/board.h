#ifndef BOARD_H
#define BOARD_H

#include <stdint.h>

#define SYSTEM_CORE_CLOCK_HZ       8000000UL

#define GPS_BAUDRATE               9600U

#define RF_FREQUENCY_MHZ           433.920f
#define RF_BITRATE_BPS             1200U
#define RF_POWER_LEVEL             0x00U
#define AX25_PREAMBLE_FLAGS        40U
#define AX25_MAX_INFO_BYTES        46U
#define AX25_MAX_FRAME_BYTES       (1U + 14U + 2U + AX25_MAX_INFO_BYTES + 2U + 1U)
#define AX25_STUFFING_MARGIN_BYTES 12U
#define RF_EST_TX_AIRTIME_MS       (((((AX25_PREAMBLE_FLAGS + AX25_MAX_FRAME_BYTES + AX25_STUFFING_MARGIN_BYTES) * 8U) * 1000U) + RF_BITRATE_BPS - 1U) / RF_BITRATE_BPS)

#define AX25_DEST_CALLSIGN         "APRS"
#define AX25_DEST_SSID             0U
#define AX25_SOURCE_CALLSIGN       "RS41"
#define AX25_SOURCE_SSID           11U

/*
 * Czech SRD default used here:
 * 433.05-434.79 MHz, 10 mW e.r.p., 10 % duty cycle.
 * Keep the interval conservative to stay below 10 % with the current frame length.
 */
#define CZ_433_MAX_DUTY_PERCENT    10U
#define TELEMETRY_INTERVAL_MS      10000U

#define VBAT_DIVIDER_MILLI_RATIO   2000U
#define MCU_VREF_MV                3300U

#define GPS_UART_TIMEOUT_MS        2000U

#endif
