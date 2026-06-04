#pragma once

#include <stdint.h>

#include "esp_err.h"
#include "esp_system.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

typedef enum {
    DIAG_TASK_SENSOR = 0,
    DIAG_TASK_LED,
    DIAG_TASK_WEBSOCKET,
    DIAG_TASK_ENGINE,
    DIAG_TASK_COUNT,
} diagnostics_task_id_t;

typedef struct {
    uint64_t uptime_ms;
    uint32_t free_heap_bytes;
    uint32_t min_free_heap_bytes;
    uint32_t largest_free_block_bytes;
    esp_reset_reason_t reset_reason;
    uint8_t task_core[DIAG_TASK_COUNT];
    uint32_t task_stack_hwm_words[DIAG_TASK_COUNT];
} diagnostics_snapshot_t;

void diagnostics_log_boot(void);
void diagnostics_register_task(diagnostics_task_id_t id, TaskHandle_t handle, BaseType_t core_id);
esp_err_t diagnostics_get_snapshot(diagnostics_snapshot_t *out_snapshot);
