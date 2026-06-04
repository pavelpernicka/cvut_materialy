#pragma once

#include <stddef.h>

#include "esp_err.h"

esp_err_t template_fields_render(const char *input, char *output, size_t output_size);
