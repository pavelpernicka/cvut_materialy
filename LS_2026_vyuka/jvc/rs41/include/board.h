#ifndef BOARD_H
#define BOARD_H

#include <stdint.h>

#define SYSTEM_CORE_CLOCK_HZ       8000000UL

#define GPS_BAUDRATE               9600U

#define RF_FREQUENCY_MHZ           433.920f
#define RF_BITRATE_BPS             2400U
#define RF_POWER_LEVEL             0x00U
#define RF_DEVIATION_LEVEL         0x08U
#define RF_PREAMBLE_BYTES          32U
#define RF_SYNC_BYTES              2U
#define RF_SYNC_WORD_0             0x2DU
#define RF_SYNC_WORD_1             0xD4U
#define RF_PACKET_REPEATS          3U
#define RF_INTER_PACKET_GAP_MS     20U
#define TELEMETRY_PACKET_BYTES     48U
#define RF_SINGLE_PACKET_AIRTIME_MS (((((RF_PREAMBLE_BYTES + RF_SYNC_BYTES + TELEMETRY_PACKET_BYTES) * 8U) * 1000U) + RF_BITRATE_BPS - 1U) / RF_BITRATE_BPS)
#define RF_EST_TX_AIRTIME_MS       ((RF_SINGLE_PACKET_AIRTIME_MS * RF_PACKET_REPEATS) + (RF_INTER_PACKET_GAP_MS * (RF_PACKET_REPEATS - 1U)))

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
