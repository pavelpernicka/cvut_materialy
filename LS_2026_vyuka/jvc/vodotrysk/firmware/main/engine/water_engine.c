#include "engine/water_engine.h"

#include <string.h>

#include "drivers/shiftreg.h"
#include "engine/queue.h"
#include "engine/renderer.h"
#include "esp_check.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "system/diagnostics.h"

static const char *TAG = "water_engine";
static const BaseType_t WATER_ENGINE_CORE = 1;
static water_engine_status_t s_status = {
    .state = WATER_ENGINE_IDLE,
    .frame_period_ms = 35,
    .fps = 1000 / 35,
    .core_id = 1,
};
static TaskHandle_t s_task;
static SemaphoreHandle_t s_mutex;
static rendered_sequence_t s_current_sequence;
static size_t s_current_frame_index;
static char s_active_playlist_id[32] = "playlist-main";
static size_t s_active_playlist_screen_index;
static uint8_t s_active_playlist_repeat_left;

static void set_active_screen_id(const char *screen_id)
{
    strlcpy(s_status.screen_id, screen_id == NULL ? "" : screen_id, sizeof(s_status.screen_id));
}

static void current_sequence_clear(void)
{
    renderer_free_sequence(&s_current_sequence);
    memset(&s_current_sequence, 0, sizeof(s_current_sequence));
    s_current_frame_index = 0;
}

static esp_err_t load_next_playlist_sequence(void)
{
    const playlist_model_t *playlist = show_model_get_playlist_by_id(s_active_playlist_id);
    if (playlist == NULL || playlist->item_count == 0) {
        return ESP_ERR_NOT_FOUND;
    }
    if (s_active_playlist_screen_index >= playlist->item_count) {
        if (!playlist->loop) {
            return ESP_ERR_NOT_FOUND;
        }
        s_active_playlist_screen_index = 0;
    }

    playlist_item_t item = playlist->items[s_active_playlist_screen_index];
    if (!item.enabled || item.screen_id[0] == '\0') {
        s_active_playlist_screen_index++;
        s_active_playlist_repeat_left = 0;
        return ESP_ERR_NOT_FOUND;
    }
    if (s_active_playlist_repeat_left == 0) {
        s_active_playlist_repeat_left = item.repeat_count == 0 ? 1 : item.repeat_count;
    }

    const screen_model_t *screen = show_model_get_screen_by_id(item.screen_id);
    if (screen == NULL || !screen->enabled) {
        s_active_playlist_screen_index++;
        s_active_playlist_repeat_left = 0;
        return ESP_ERR_NOT_FOUND;
    }
    if (s_active_playlist_repeat_left > 0) {
        s_active_playlist_repeat_left--;
    }
    if (s_active_playlist_repeat_left == 0) {
        s_active_playlist_screen_index++;
    }
    current_sequence_clear();
    strlcpy(s_status.playlist_id, s_active_playlist_id, sizeof(s_status.playlist_id));
    set_active_screen_id(item.screen_id);
    return renderer_render_screen(screen, &s_current_sequence);
}

static esp_err_t load_next_sequence(void)
{
    queue_item_t item;
    if (queue_pop(&item) == ESP_OK) {
        current_sequence_clear();
        s_current_sequence = item.sequence;
        s_current_frame_index = 0;
        s_status.state = WATER_ENGINE_PLAYING_GUEST_ITEM;
        set_active_screen_id(item.id);
        return ESP_OK;
    }
    s_status.state = WATER_ENGINE_PLAYING_SHOW;
    return load_next_playlist_sequence();
}

static void water_engine_task(void *arg)
{
    (void) arg;

    while (true) {
        if (s_status.state == WATER_ENGINE_PAUSED) {
            vTaskDelay(pdMS_TO_TICKS(50));
            continue;
        }
        if (s_status.state == WATER_ENGINE_IDLE) {
            shiftreg_all_off();
            vTaskDelay(pdMS_TO_TICKS(50));
            continue;
        }

        if (s_current_sequence.frames == NULL || s_current_frame_index >= s_current_sequence.frame_count) {
            if (load_next_sequence() != ESP_OK) {
                s_status.state = WATER_ENGINE_IDLE;
                set_active_screen_id("");
                shiftreg_all_off();
                vTaskDelay(pdMS_TO_TICKS(50));
                continue;
            }
        }

        water_frame_t frame = s_current_sequence.frames[s_current_frame_index++];
        s_status.active_mask = frame.valves;
        s_status.frame_period_ms = frame.duration_ms;
        s_status.fps = frame.duration_ms == 0 ? 0 : 1000 / frame.duration_ms;
        (void) shiftreg_write_u64(frame.valves);
        vTaskDelay(pdMS_TO_TICKS(frame.duration_ms == 0 ? 35 : frame.duration_ms));
    }
}

esp_err_t water_engine_init(void)
{
    if (s_task != NULL) {
        return ESP_OK;
    }
    const playlist_model_t *default_playlist = show_model_get_default_playlist();
    if (default_playlist != NULL) {
        strlcpy(s_active_playlist_id, default_playlist->id, sizeof(s_active_playlist_id));
        strlcpy(s_status.playlist_id, default_playlist->id, sizeof(s_status.playlist_id));
    }
    s_mutex = xSemaphoreCreateMutex();
    if (s_mutex == NULL) {
        return ESP_ERR_NO_MEM;
    }

    BaseType_t ok = xTaskCreatePinnedToCore(
        water_engine_task,
        "water_engine",
        6144,
        NULL,
        configMAX_PRIORITIES - 2,
        &s_task,
        WATER_ENGINE_CORE);
    if (ok != pdPASS) {
        return ESP_FAIL;
    }
    diagnostics_register_task(DIAG_TASK_ENGINE, s_task, WATER_ENGINE_CORE);

    ESP_LOGI(TAG, "Water engine task created");
    return ESP_OK;
}

esp_err_t water_engine_start(void)
{
    s_status.state = WATER_ENGINE_PLAYING_SHOW;
    return ESP_OK;
}

esp_err_t water_engine_stop(void)
{
    s_status.state = WATER_ENGINE_IDLE;
    s_status.active_mask = 0;
    current_sequence_clear();
    set_active_screen_id("");
    shiftreg_all_off();
    return ESP_OK;
}

esp_err_t water_engine_pause(void)
{
    s_status.state = WATER_ENGINE_PAUSED;
    return ESP_OK;
}

esp_err_t water_engine_resume(void)
{
    s_status.state = WATER_ENGINE_PLAYING_SHOW;
    return ESP_OK;
}

esp_err_t water_engine_next(void)
{
    current_sequence_clear();
    if (s_status.state == WATER_ENGINE_IDLE || s_status.state == WATER_ENGINE_PAUSED) {
        s_status.state = WATER_ENGINE_PLAYING_SHOW;
    }
    return ESP_OK;
}

esp_err_t water_engine_all_off(void)
{
    current_sequence_clear();
    s_status.active_mask = 0;
    set_active_screen_id("");
    shiftreg_all_off();
    return ESP_OK;
}

esp_err_t water_engine_set_live_mask(uint64_t mask)
{
    current_sequence_clear();
    s_status.active_mask = mask;
    s_status.state = WATER_ENGINE_PLAYING_GUEST_ITEM;
    set_active_screen_id("live-mask");
    return shiftreg_write_u64(mask);
}

esp_err_t water_engine_drain_pulse(uint32_t duration_ms)
{
    current_sequence_clear();
    s_status.active_mask = UINT64_MAX;
    s_status.state = WATER_ENGINE_PLAYING_GUEST_ITEM;
    set_active_screen_id("drain");
    ESP_ERROR_CHECK(shiftreg_write_u64(UINT64_MAX));
    vTaskDelay(pdMS_TO_TICKS(duration_ms));
    s_status.active_mask = 0;
    shiftreg_all_off();
    s_status.state = WATER_ENGINE_IDLE;
    set_active_screen_id("");
    return ESP_OK;
}

esp_err_t water_engine_play_screen_now(const char *screen_id)
{
    const screen_model_t *screen = show_model_get_screen_by_id(screen_id);
    if (screen == NULL) {
        return ESP_ERR_NOT_FOUND;
    }
    current_sequence_clear();
    ESP_RETURN_ON_ERROR(renderer_render_screen(screen, &s_current_sequence), TAG, "render screen failed");
    s_status.state = WATER_ENGINE_PLAYING_GUEST_ITEM;
    set_active_screen_id(screen_id);
    return ESP_OK;
}

esp_err_t water_engine_start_playlist(const char *playlist_id)
{
    if (playlist_id == NULL || show_model_get_playlist_by_id(playlist_id) == NULL) {
        return ESP_ERR_NOT_FOUND;
    }
    strlcpy(s_active_playlist_id, playlist_id, sizeof(s_active_playlist_id));
    strlcpy(s_status.playlist_id, playlist_id, sizeof(s_status.playlist_id));
    s_active_playlist_screen_index = 0;
    s_active_playlist_repeat_left = 0;
    current_sequence_clear();
    set_active_screen_id("");
    s_status.state = WATER_ENGINE_PLAYING_SHOW;
    return ESP_OK;
}

water_engine_status_t water_engine_get_status(void)
{
    return s_status;
}
