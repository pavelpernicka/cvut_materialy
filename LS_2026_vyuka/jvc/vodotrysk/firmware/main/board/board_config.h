#pragma once

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    int pin_pump1;
    int pin_pump2;
    bool invert_shift_outputs;
    bool shift_msb_first;
    bool pump_outputs_inverted;
} board_config_t;

// Default keeps PUMP1 on GPIO15 because GPIO45 is an ESP32-S3 strapping pin.
const board_config_t *board_config_get(void);
