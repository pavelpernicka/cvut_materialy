#pragma once

#include "esp_err.h"
#include "esp_http_server.h"

esp_err_t websocket_init(void);
esp_err_t websocket_register_httpd(httpd_handle_t server);
