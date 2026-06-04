#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "esp_err.h"
#include "engine/show_model.h"

typedef struct {
    uint64_t valves;
    uint16_t duration_ms;
} water_frame_t;

typedef struct {
    water_frame_t *frames;
    size_t frame_count;
    bool owns_memory;
} rendered_sequence_t;

typedef enum {
    WATER_ENGINE_IDLE = 0,
    WATER_ENGINE_PLAYING_SHOW,
    WATER_ENGINE_PLAYING_GUEST_ITEM,
    WATER_ENGINE_PAUSED,
    WATER_ENGINE_ERROR,
    WATER_ENGINE_EMERGENCY_STOP,
} water_engine_state_t;

typedef struct {
    water_engine_state_t state;
    uint64_t active_mask;
    uint32_t frame_period_ms;
    uint32_t fps;
    uint8_t core_id;
    char playlist_id[32];
    char screen_id[32];
} water_engine_status_t;

esp_err_t water_engine_init(void);
esp_err_t water_engine_start(void);
esp_err_t water_engine_stop(void);
esp_err_t water_engine_pause(void);
esp_err_t water_engine_resume(void);
esp_err_t water_engine_next(void);
esp_err_t water_engine_all_off(void);
esp_err_t water_engine_set_live_mask(uint64_t mask);
esp_err_t water_engine_drain_pulse(uint32_t duration_ms);
esp_err_t water_engine_play_screen_now(const char *screen_id);
esp_err_t water_engine_start_playlist(const char *playlist_id);
water_engine_status_t water_engine_get_status(void);
