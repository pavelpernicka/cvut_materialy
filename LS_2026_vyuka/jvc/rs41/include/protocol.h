#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stddef.h>
#include <stdint.h>

#include "gps.h"

#include "board.h"

#define TELEMETRY_PROTOCOL_VERSION 2U

size_t protocol_build_packet(uint8_t *packet,
                             uint32_t uptime_ms,
                             const gps_fix_t *fix,
                             uint16_t battery_mv,
                             int16_t mcu_temp_centi);

#endif
