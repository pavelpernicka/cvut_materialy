#include "system/diagnostics.h"

#include <string.h>

#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_system.h"
#include "esp_timer.h"

static const char *TAG = "diagnostics";
static TaskHandle_t s_task_handles[DIAG_TASK_COUNT];
static uint8_t s_task_cores[DIAG_TASK_COUNT];

void diagnostics_log_boot(void)
{
    ESP_LOGI(TAG, "Firmware boot");
    ESP_LOGI(TAG, "Reset reason: %d", (int) esp_reset_reason());
}

void diagnostics_register_task(diagnostics_task_id_t id, TaskHandle_t handle, BaseType_t core_id)
{
    if (id >= DIAG_TASK_COUNT) {
        return;
    }
    s_task_handles[id] = handle;
    s_task_cores[id] = core_id < 0 ? UINT8_MAX : (uint8_t) core_id;
}

esp_err_t diagnostics_get_snapshot(diagnostics_snapshot_t *out_snapshot)
{
    if (out_snapshot == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    memset(out_snapshot, 0, sizeof(*out_snapshot));
    out_snapshot->uptime_ms = (uint64_t) (esp_timer_get_time() / 1000ULL);
    out_snapshot->free_heap_bytes = (uint32_t) esp_get_free_heap_size();
    out_snapshot->min_free_heap_bytes = (uint32_t) esp_get_minimum_free_heap_size();
    out_snapshot->largest_free_block_bytes = (uint32_t) heap_caps_get_largest_free_block(MALLOC_CAP_DEFAULT);
    out_snapshot->reset_reason = esp_reset_reason();

    for (size_t i = 0; i < DIAG_TASK_COUNT; ++i) {
        out_snapshot->task_core[i] = s_task_cores[i];
        if (s_task_handles[i] != NULL) {
            out_snapshot->task_stack_hwm_words[i] = (uint32_t) uxTaskGetStackHighWaterMark(s_task_handles[i]);
        }
    }

    return ESP_OK;
}
