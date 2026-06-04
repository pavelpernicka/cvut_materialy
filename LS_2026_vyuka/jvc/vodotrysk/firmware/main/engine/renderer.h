#pragma once

#include "engine/show_model.h"
#include "engine/water_engine.h"
#include "esp_err.h"

esp_err_t renderer_render_screen(const screen_model_t *screen, rendered_sequence_t *out_sequence);
void renderer_free_sequence(rendered_sequence_t *sequence);
