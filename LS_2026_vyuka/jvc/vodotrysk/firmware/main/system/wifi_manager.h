#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"
#include "system/config.h"

typedef struct {
    char mode[16];
    char ip[16];
    char ssid[32];
    int8_t rssi;
    bool sta_has_ip;
    bool ap_active;
    bool fallback_ap;
} wifi_status_t;

esp_err_t wifi_manager_init(void);
esp_err_t wifi_manager_apply_config(const wifi_config_model_t *cfg);
esp_err_t wifi_manager_reconnect(void);
wifi_status_t wifi_manager_get_status(void);
const char *wifi_manager_get_ip(void);
const char *wifi_manager_get_mode(void);
