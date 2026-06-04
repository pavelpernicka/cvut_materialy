#pragma once

#include "esp_err.h"
#include "system/config.h"

esp_err_t storage_init(void);
esp_err_t storage_load_config(app_config_t *out_config);
esp_err_t storage_save_config(const app_config_t *config);
