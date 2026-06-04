#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "esp_err.h"

typedef enum {
    SCREEN_TEXT = 0,
    SCREEN_BITMAP,
    SCREEN_SENSOR,
    SCREEN_CLOCK,
    SCREEN_TEST,
} screen_type_t;

typedef enum {
    SCREEN_LAYOUT_SCROLL = 0,
    SCREEN_LAYOUT_CENTER,
    SCREEN_LAYOUT_STATIC,
} screen_layout_t;

#define SCREEN_BITMAP_MAX_FRAMES 64
#define SCREEN_BITMAP_HEX_LEN ((SCREEN_BITMAP_MAX_FRAMES * 16) + 1)
#define PLAYLIST_MAX_ITEMS 16

typedef struct {
    char screen_id[32];
    bool enabled;
    uint8_t repeat_count;
} playlist_item_t;

typedef struct {
    char id[32];
    char name[64];
    screen_type_t type;
    uint32_t duration_ms;
    uint32_t hold_ms;
    bool enabled;
    bool rich_text;
    uint8_t repeat_count;
    uint8_t gap_columns;
    screen_layout_t layout;
    char text[128];
    uint8_t bitmap_frames;
    char bitmap[SCREEN_BITMAP_HEX_LEN];
} screen_model_t;

typedef struct {
    char id[32];
    char name[64];
    bool loop;
    bool is_default_idle;
    uint8_t item_count;
    playlist_item_t items[PLAYLIST_MAX_ITEMS];
} playlist_model_t;

void show_model_init(void);
size_t show_model_get_screen_count(void);
size_t show_model_get_playlist_count(void);
const screen_model_t *show_model_get_screen_by_index(size_t index);
const screen_model_t *show_model_get_screen_by_id(const char *id);
const playlist_model_t *show_model_get_playlist_by_index(size_t index);
const playlist_model_t *show_model_get_playlist_by_id(const char *id);
const playlist_model_t *show_model_get_default_playlist(void);
esp_err_t show_model_upsert_screen(const screen_model_t *screen);
esp_err_t show_model_upsert_playlist(const playlist_model_t *playlist);
esp_err_t show_model_delete_screen(const char *id);
esp_err_t show_model_delete_playlist(const char *id);
esp_err_t show_model_export_json(char *screens_json, size_t screens_size, char *playlists_json, size_t playlists_size);
esp_err_t show_model_import_json(const char *screens_json, const char *playlists_json);
