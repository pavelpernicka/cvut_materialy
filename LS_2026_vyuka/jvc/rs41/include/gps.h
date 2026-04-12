#ifndef GPS_H
#define GPS_H

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    int32_t latitude_e7;
    int32_t longitude_e7;
    int32_t altitude_cm;
    uint16_t speed_cms;
    uint8_t satellites;
    uint8_t flags;
    uint32_t last_update_ms;
} gps_fix_t;

#define GPS_FLAG_POSITION_VALID    (1U << 0)
#define GPS_FLAG_ALTITUDE_VALID    (1U << 1)
#define GPS_FLAG_SPEED_VALID       (1U << 2)

void gps_init(void);
void gps_poll(void);
const gps_fix_t *gps_get_fix(void);

#endif
