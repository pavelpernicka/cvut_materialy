#include "board/board_config.h"

#include "board/pinmap.h"

static const board_config_t s_board_config = {
    .pin_pump1 = PIN_SW_PUMP1_RECOMMENDED,
    .pin_pump2 = PIN_SW_PUMP2,
    .invert_shift_outputs = false,
    .shift_msb_first = true,
    .pump_outputs_inverted = false,
};

const board_config_t *board_config_get(void)
{
    return &s_board_config;
}
