#include "system/websocket.h"

#include <inttypes.h>
#include <stdio.h>
#include <string.h>

#include "drivers/pumps.h"
#include "drivers/sensors.h"
#include "engine/queue.h"
#include "engine/water_engine.h"
#include "esp_http_server.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "system/diagnostics.h"
#include "system/wifi_manager.h"

static const char *TAG = "websocket";
static const BaseType_t WS_CORE = 0;
static httpd_handle_t s_server;
static TaskHandle_t s_ws_task;

static esp_err_t ws_snapshot_build(char *body, size_t body_size)
{
    const sensor_snapshot_t *s = sensors_get_cached();
    pump_state_t p1;
    pump_state_t p2;
    pumps_get_state(0, &p1);
    pumps_get_state(1, &p2);
    water_engine_status_t engine = water_engine_get_status();
    diagnostics_snapshot_t diag = {0};
    (void) diagnostics_get_snapshot(&diag);

    int written = snprintf(
        body,
        body_size,
        "{\"type\":\"snapshot\",\"status\":{\"ip\":\"%s\",\"mode\":\"%s\",\"queue_len\":%u,\"engine_state\":%u},"
        "\"sensors\":{\"level_low\":%s,\"level_high\":%s,\"water_state\":%u,\"temp\":%.1f,\"humidity\":%.1f,\"unix_time\":%" PRIu64 "},"
        "\"pumps\":{\"pump1\":{\"on\":%s,\"auto_enabled\":%s,\"manual_override\":%s,\"timed_out\":%s,\"current\":%.3f},"
        "\"pump2\":{\"on\":%s,\"auto_enabled\":%s,\"manual_override\":%s,\"timed_out\":%s,\"current\":%.3f}},"
        "\"engine\":{\"frame_period_ms\":%u,\"fps\":%u,\"core\":%u,\"playlist_id\":\"%s\",\"screen_id\":\"%s\"},"
        "\"diagnostics\":{\"uptime_ms\":%" PRIu64 ",\"free_heap_bytes\":%u,\"min_free_heap_bytes\":%u,\"largest_free_block_bytes\":%u,"
        "\"task_core\":[%u,%u,%u,%u],\"task_stack_hwm_words\":[%u,%u,%u,%u]}}",
        wifi_manager_get_ip(),
        wifi_manager_get_mode(),
        (unsigned) queue_len(),
        (unsigned) engine.state,
        s->level_low ? "true" : "false",
        s->level_high ? "true" : "false",
        (unsigned) s->water_state,
        (double) s->temperature_c,
        (double) s->humidity_pct,
        s->unix_time,
        p1.output_on ? "true" : "false",
        p1.auto_enabled ? "true" : "false",
        p1.manual_override ? "true" : "false",
        p1.timed_out ? "true" : "false",
        (double) p1.current_a,
        p2.output_on ? "true" : "false",
        p2.auto_enabled ? "true" : "false",
        p2.manual_override ? "true" : "false",
        p2.timed_out ? "true" : "false",
        (double) p2.current_a,
        (unsigned) engine.frame_period_ms,
        (unsigned) engine.fps,
        (unsigned) engine.core_id,
        engine.playlist_id,
        engine.screen_id,
        diag.uptime_ms,
        (unsigned) diag.free_heap_bytes,
        (unsigned) diag.min_free_heap_bytes,
        (unsigned) diag.largest_free_block_bytes,
        (unsigned) diag.task_core[DIAG_TASK_SENSOR],
        (unsigned) diag.task_core[DIAG_TASK_LED],
        (unsigned) diag.task_core[DIAG_TASK_WEBSOCKET],
        (unsigned) diag.task_core[DIAG_TASK_ENGINE],
        (unsigned) diag.task_stack_hwm_words[DIAG_TASK_SENSOR],
        (unsigned) diag.task_stack_hwm_words[DIAG_TASK_LED],
        (unsigned) diag.task_stack_hwm_words[DIAG_TASK_WEBSOCKET],
        (unsigned) diag.task_stack_hwm_words[DIAG_TASK_ENGINE]);

    return (written > 0 && (size_t) written < body_size) ? ESP_OK : ESP_ERR_NO_MEM;
}

static esp_err_t ws_handler(httpd_req_t *req)
{
    httpd_ws_frame_t frame = {0};
    frame.type = HTTPD_WS_TYPE_TEXT;
    if (httpd_ws_recv_frame(req, &frame, 0) != ESP_OK) {
        return ESP_FAIL;
    }

    if (frame.len > 0) {
        uint8_t payload[64];
        frame.payload = payload;
        if (httpd_ws_recv_frame(req, &frame, sizeof(payload) - 1) != ESP_OK) {
            return ESP_FAIL;
        }
        payload[frame.len < sizeof(payload) ? frame.len : sizeof(payload) - 1] = '\0';
    }

    char body[512];
    if (ws_snapshot_build(body, sizeof(body)) != ESP_OK) {
        return ESP_FAIL;
    }

    httpd_ws_frame_t response = {
        .type = HTTPD_WS_TYPE_TEXT,
        .payload = (uint8_t *) body,
        .len = strlen(body),
    };
    return httpd_ws_send_frame(req, &response);
}

static void websocket_task(void *arg)
{
    (void) arg;

    while (true) {
        if (s_server != NULL) {
            size_t client_count = 8;
            int client_fds[8] = {0};
            if (httpd_get_client_list(s_server, &client_count, client_fds) == ESP_OK && client_count > 0) {
                char body[512];
                if (ws_snapshot_build(body, sizeof(body)) == ESP_OK) {
                    httpd_ws_frame_t frame = {
                        .type = HTTPD_WS_TYPE_TEXT,
                        .payload = (uint8_t *) body,
                        .len = strlen(body),
                    };
                    for (size_t i = 0; i < client_count; ++i) {
                        if (httpd_ws_get_fd_info(s_server, client_fds[i]) == HTTPD_WS_CLIENT_WEBSOCKET) {
                            (void) httpd_ws_send_data(s_server, client_fds[i], &frame);
                        }
                    }
                }
            }
        }
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

esp_err_t websocket_init(void)
{
    if (s_ws_task != NULL) {
        return ESP_OK;
    }

    BaseType_t ok = xTaskCreatePinnedToCore(
        websocket_task,
        "ws_broadcast",
        4096,
        NULL,
        3,
        &s_ws_task,
        WS_CORE);
    if (ok != pdPASS) {
        ESP_LOGE(TAG, "Failed to create websocket task");
        return ESP_FAIL;
    }
    diagnostics_register_task(DIAG_TASK_WEBSOCKET, s_ws_task, WS_CORE);
    return ESP_OK;
}

esp_err_t websocket_register_httpd(httpd_handle_t server)
{
    if (server == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    s_server = server;

    httpd_uri_t ws_uri = {
        .uri = "/ws",
        .method = HTTP_GET,
        .handler = ws_handler,
        .is_websocket = true,
    };
    return httpd_register_uri_handler(server, &ws_uri);
}
