#include "engine/show_model.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SHOW_MODEL_MAX_SCREENS 16
#define SHOW_MODEL_MAX_PLAYLISTS 8
#define SHOW_MODEL_SCREENS_PATH "/config/screens.json"
#define SHOW_MODEL_PLAYLISTS_PATH "/config/playlists.json"

static screen_model_t s_screens[SHOW_MODEL_MAX_SCREENS];
static size_t s_screen_count;
static playlist_model_t s_playlists[SHOW_MODEL_MAX_PLAYLISTS];
static size_t s_playlist_count;

static bool parse_bool_after(const char *json, const char *key, bool default_value)
{
    char needle[48];
    snprintf(needle, sizeof(needle), "\"%s\":", key);
    const char *p = strstr(json, needle);
    if (p == NULL) {
        return default_value;
    }
    p += strlen(needle);
    while (*p == ' ' || *p == '\t') {
        ++p;
    }
    if (strncmp(p, "true", 4) == 0) return true;
    if (strncmp(p, "false", 5) == 0) return false;
    return default_value;
}

static uint32_t parse_u32_after(const char *json, const char *key, uint32_t default_value)
{
    char needle[48];
    snprintf(needle, sizeof(needle), "\"%s\":", key);
    const char *p = strstr(json, needle);
    if (p == NULL) {
        return default_value;
    }
    p += strlen(needle);
    return (uint32_t) strtoul(p, NULL, 10);
}

static void parse_string_after(const char *json, const char *key, char *out, size_t out_size)
{
    char needle[48];
    snprintf(needle, sizeof(needle), "\"%s\":\"", key);
    const char *p = strstr(json, needle);
    if (p == NULL) {
        out[0] = '\0';
        return;
    }
    p += strlen(needle);
    size_t i = 0;
    while (p[i] != '\0' && p[i] != '"' && i + 1 < out_size) {
        out[i] = p[i];
        ++i;
    }
    out[i] = '\0';
}

static esp_err_t read_file_to_buffer(const char *path, char **out)
{
    FILE *f = fopen(path, "rb");
    if (f == NULL) {
        return ESP_ERR_NOT_FOUND;
    }
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    rewind(f);
    char *buf = calloc((size_t) size + 1U, 1U);
    if (buf == NULL) {
        fclose(f);
        return ESP_ERR_NO_MEM;
    }
    fread(buf, 1, (size_t) size, f);
    fclose(f);
    *out = buf;
    return ESP_OK;
}

static esp_err_t write_buffer_to_file(const char *path, const char *buf)
{
    FILE *f = fopen(path, "wb");
    if (f == NULL) {
        return ESP_FAIL;
    }
    fwrite(buf, 1, strlen(buf), f);
    fclose(f);
    return ESP_OK;
}

static void show_model_load_defaults(void)
{
    memset(s_screens, 0, sizeof(s_screens));
    memset(s_playlists, 0, sizeof(s_playlists));

    s_screen_count = 3;
    snprintf(s_screens[0].id, sizeof(s_screens[0].id), "screen-clock");
    snprintf(s_screens[0].name, sizeof(s_screens[0].name), "Clock");
    s_screens[0].type = SCREEN_CLOCK;
    s_screens[0].duration_ms = 35;
    s_screens[0].hold_ms = 400;
    s_screens[0].repeat_count = 1;
    s_screens[0].gap_columns = 8;
    s_screens[0].layout = SCREEN_LAYOUT_CENTER;
    s_screens[0].enabled = true;
    snprintf(s_screens[0].text, sizeof(s_screens[0].text), "CAS {{time}}");

    snprintf(s_screens[1].id, sizeof(s_screens[1].id), "screen-temp");
    snprintf(s_screens[1].name, sizeof(s_screens[1].name), "Temperature");
    s_screens[1].type = SCREEN_SENSOR;
    s_screens[1].duration_ms = 35;
    s_screens[1].hold_ms = 400;
    s_screens[1].repeat_count = 1;
    s_screens[1].gap_columns = 8;
    s_screens[1].layout = SCREEN_LAYOUT_SCROLL;
    s_screens[1].enabled = true;
    s_screens[1].rich_text = true;
    snprintf(s_screens[1].text, sizeof(s_screens[1].text), "T {{temp}} [gap=4] H {{humidity}}");

    snprintf(s_screens[2].id, sizeof(s_screens[2].id), "screen-welcome");
    snprintf(s_screens[2].name, sizeof(s_screens[2].name), "Welcome");
    s_screens[2].type = SCREEN_TEXT;
    s_screens[2].duration_ms = 28;
    s_screens[2].hold_ms = 0;
    s_screens[2].repeat_count = 1;
    s_screens[2].gap_columns = 10;
    s_screens[2].layout = SCREEN_LAYOUT_SCROLL;
    s_screens[2].enabled = true;
    s_screens[2].rich_text = true;
    snprintf(s_screens[2].text, sizeof(s_screens[2].text), "[speed=24]AHOJ [gap=6] VODNI OPONA");

    s_playlist_count = 1;
    snprintf(s_playlists[0].id, sizeof(s_playlists[0].id), "playlist-main");
    snprintf(s_playlists[0].name, sizeof(s_playlists[0].name), "Main loop");
    s_playlists[0].loop = true;
    s_playlists[0].is_default_idle = true;
    s_playlists[0].item_count = 3;
    snprintf(s_playlists[0].items[0].screen_id, sizeof(s_playlists[0].items[0].screen_id), "screen-clock");
    s_playlists[0].items[0].enabled = true;
    s_playlists[0].items[0].repeat_count = 1;
    snprintf(s_playlists[0].items[1].screen_id, sizeof(s_playlists[0].items[1].screen_id), "screen-temp");
    s_playlists[0].items[1].enabled = true;
    s_playlists[0].items[1].repeat_count = 1;
    snprintf(s_playlists[0].items[2].screen_id, sizeof(s_playlists[0].items[2].screen_id), "screen-welcome");
    s_playlists[0].items[2].enabled = true;
    s_playlists[0].items[2].repeat_count = 1;
}

static esp_err_t show_model_save_screens(void)
{
    char buf[12288];
    int cursor = snprintf(buf, sizeof(buf), "[");
    for (size_t i = 0; i < s_screen_count; ++i) {
        cursor += snprintf(
            buf + cursor,
            sizeof(buf) - (size_t) cursor,
            "%s{\"id\":\"%s\",\"name\":\"%s\",\"type\":%u,\"duration_ms\":%u,\"hold_ms\":%u,\"enabled\":%s,"
            "\"rich_text\":%s,\"repeat_count\":%u,\"gap_columns\":%u,\"layout\":%u,\"text\":\"%s\",\"bitmap_frames\":%u,\"bitmap\":\"%s\"}",
            i == 0 ? "" : ",",
            s_screens[i].id,
            s_screens[i].name,
            (unsigned) s_screens[i].type,
            (unsigned) s_screens[i].duration_ms,
            (unsigned) s_screens[i].hold_ms,
            s_screens[i].enabled ? "true" : "false",
            s_screens[i].rich_text ? "true" : "false",
            (unsigned) s_screens[i].repeat_count,
            (unsigned) s_screens[i].gap_columns,
            (unsigned) s_screens[i].layout,
            s_screens[i].text,
            (unsigned) s_screens[i].bitmap_frames,
            s_screens[i].bitmap);
    }
    snprintf(buf + cursor, sizeof(buf) - (size_t) cursor, "]");
    return write_buffer_to_file(SHOW_MODEL_SCREENS_PATH, buf);
}

static esp_err_t show_model_save_playlists(void)
{
    char buf[8192];
    int cursor = snprintf(buf, sizeof(buf), "[");
    for (size_t i = 0; i < s_playlist_count; ++i) {
        cursor += snprintf(
            buf + cursor,
            sizeof(buf) - (size_t) cursor,
            "%s{\"id\":\"%s\",\"name\":\"%s\",\"loop\":%s,\"is_default_idle\":%s,\"items\":[",
            i == 0 ? "" : ",",
            s_playlists[i].id,
            s_playlists[i].name,
            s_playlists[i].loop ? "true" : "false",
            s_playlists[i].is_default_idle ? "true" : "false");
        for (size_t j = 0; j < s_playlists[i].item_count; ++j) {
            cursor += snprintf(
                buf + cursor,
                sizeof(buf) - (size_t) cursor,
                "%s{\"screen_id\":\"%s\",\"enabled\":%s,\"repeat_count\":%u}",
                j == 0 ? "" : ",",
                s_playlists[i].items[j].screen_id,
                s_playlists[i].items[j].enabled ? "true" : "false",
                (unsigned) s_playlists[i].items[j].repeat_count);
        }
        cursor += snprintf(buf + cursor, sizeof(buf) - (size_t) cursor, "]}");
    }
    snprintf(buf + cursor, sizeof(buf) - (size_t) cursor, "]");
    return write_buffer_to_file(SHOW_MODEL_PLAYLISTS_PATH, buf);
}

static void load_screens_from_json(const char *json)
{
    s_screen_count = 0;
    const char *cursor = json;
    while ((cursor = strchr(cursor, '{')) != NULL && s_screen_count < SHOW_MODEL_MAX_SCREENS) {
        screen_model_t *screen = &s_screens[s_screen_count];
        memset(screen, 0, sizeof(*screen));
        parse_string_after(cursor, "id", screen->id, sizeof(screen->id));
        parse_string_after(cursor, "name", screen->name, sizeof(screen->name));
        parse_string_after(cursor, "text", screen->text, sizeof(screen->text));
        parse_string_after(cursor, "bitmap", screen->bitmap, sizeof(screen->bitmap));
        screen->type = (screen_type_t) parse_u32_after(cursor, "type", SCREEN_TEXT);
        screen->duration_ms = parse_u32_after(cursor, "duration_ms", 35);
        screen->hold_ms = parse_u32_after(cursor, "hold_ms", 0);
        screen->enabled = parse_bool_after(cursor, "enabled", true);
        screen->rich_text = parse_bool_after(cursor, "rich_text", false);
        screen->repeat_count = (uint8_t) parse_u32_after(cursor, "repeat_count", 1);
        screen->gap_columns = (uint8_t) parse_u32_after(cursor, "gap_columns", 6);
        screen->layout = (screen_layout_t) parse_u32_after(cursor, "layout", SCREEN_LAYOUT_SCROLL);
        screen->bitmap_frames = (uint8_t) parse_u32_after(cursor, "bitmap_frames", 0);
        ++s_screen_count;
        ++cursor;
    }
}

static void load_playlists_from_json(const char *json)
{
    s_playlist_count = 0;
    const char *cursor = json;
    while ((cursor = strchr(cursor, '{')) != NULL && s_playlist_count < SHOW_MODEL_MAX_PLAYLISTS) {
        playlist_model_t *playlist = &s_playlists[s_playlist_count];
        memset(playlist, 0, sizeof(*playlist));
        parse_string_after(cursor, "id", playlist->id, sizeof(playlist->id));
        parse_string_after(cursor, "name", playlist->name, sizeof(playlist->name));
        playlist->loop = parse_bool_after(cursor, "loop", true);
        playlist->is_default_idle = parse_bool_after(cursor, "is_default_idle", s_playlist_count == 0);
        const char *items = strstr(cursor, "\"items\":[");
        if (items != NULL) {
            items += strlen("\"items\":[");
            while ((items = strchr(items, '{')) != NULL && playlist->item_count < PLAYLIST_MAX_ITEMS) {
                playlist_item_t *item = &playlist->items[playlist->item_count];
                memset(item, 0, sizeof(*item));
                parse_string_after(items, "screen_id", item->screen_id, sizeof(item->screen_id));
                item->enabled = parse_bool_after(items, "enabled", true);
                item->repeat_count = (uint8_t) parse_u32_after(items, "repeat_count", 1);
                ++playlist->item_count;
                ++items;
                if (strchr(items, ']') != NULL && strchr(items, '{') > strchr(items, ']')) {
                    break;
                }
            }
        }
        ++s_playlist_count;
        ++cursor;
    }
}

void show_model_init(void)
{
    show_model_load_defaults();
    char *json = NULL;
    if (read_file_to_buffer(SHOW_MODEL_SCREENS_PATH, &json) == ESP_OK) {
        load_screens_from_json(json);
        free(json);
    } else {
        (void) show_model_save_screens();
    }
    json = NULL;
    if (read_file_to_buffer(SHOW_MODEL_PLAYLISTS_PATH, &json) == ESP_OK) {
        load_playlists_from_json(json);
        free(json);
    } else {
        (void) show_model_save_playlists();
    }
}

size_t show_model_get_screen_count(void) { return s_screen_count; }
size_t show_model_get_playlist_count(void) { return s_playlist_count; }

const screen_model_t *show_model_get_screen_by_index(size_t index)
{
    return index < s_screen_count ? &s_screens[index] : NULL;
}

const screen_model_t *show_model_get_screen_by_id(const char *id)
{
    for (size_t i = 0; i < s_screen_count; ++i) {
        if (strcmp(s_screens[i].id, id) == 0) return &s_screens[i];
    }
    return NULL;
}

const playlist_model_t *show_model_get_playlist_by_index(size_t index)
{
    return index < s_playlist_count ? &s_playlists[index] : NULL;
}

const playlist_model_t *show_model_get_playlist_by_id(const char *id)
{
    for (size_t i = 0; i < s_playlist_count; ++i) {
        if (strcmp(s_playlists[i].id, id) == 0) return &s_playlists[i];
    }
    return NULL;
}

const playlist_model_t *show_model_get_default_playlist(void)
{
    for (size_t i = 0; i < s_playlist_count; ++i) {
        if (s_playlists[i].is_default_idle) {
            return &s_playlists[i];
        }
    }
    return s_playlist_count > 0 ? &s_playlists[0] : NULL;
}

esp_err_t show_model_upsert_screen(const screen_model_t *screen)
{
    if (screen == NULL || screen->id[0] == '\0') return ESP_ERR_INVALID_ARG;
    screen_model_t normalized = *screen;
    if (normalized.bitmap_frames > SCREEN_BITMAP_MAX_FRAMES) {
        normalized.bitmap_frames = SCREEN_BITMAP_MAX_FRAMES;
    }
    if (normalized.repeat_count == 0) {
        normalized.repeat_count = 1;
    }
    normalized.bitmap[SCREEN_BITMAP_HEX_LEN - 1] = '\0';
    if (normalized.type != SCREEN_BITMAP) {
        normalized.bitmap_frames = 0;
        normalized.bitmap[0] = '\0';
    }
    for (size_t i = 0; i < s_screen_count; ++i) {
        if (strcmp(s_screens[i].id, normalized.id) == 0) {
            s_screens[i] = normalized;
            return show_model_save_screens();
        }
    }
    if (s_screen_count >= SHOW_MODEL_MAX_SCREENS) return ESP_ERR_NO_MEM;
    s_screens[s_screen_count++] = normalized;
    return show_model_save_screens();
}

esp_err_t show_model_upsert_playlist(const playlist_model_t *playlist)
{
    if (playlist == NULL || playlist->id[0] == '\0') return ESP_ERR_INVALID_ARG;
    playlist_model_t normalized = *playlist;
    if (normalized.item_count > PLAYLIST_MAX_ITEMS) {
        normalized.item_count = PLAYLIST_MAX_ITEMS;
    }
    if (normalized.is_default_idle) {
        for (size_t i = 0; i < s_playlist_count; ++i) {
            s_playlists[i].is_default_idle = false;
        }
    }
    for (size_t i = 0; i < normalized.item_count; ++i) {
        if (normalized.items[i].repeat_count == 0) {
            normalized.items[i].repeat_count = 1;
        }
    }
    for (size_t i = 0; i < s_playlist_count; ++i) {
        if (strcmp(s_playlists[i].id, normalized.id) == 0) {
            s_playlists[i] = normalized;
            return show_model_save_playlists();
        }
    }
    if (s_playlist_count >= SHOW_MODEL_MAX_PLAYLISTS) return ESP_ERR_NO_MEM;
    s_playlists[s_playlist_count++] = normalized;
    return show_model_save_playlists();
}

esp_err_t show_model_delete_screen(const char *id)
{
    if (id == NULL || id[0] == '\0') {
        return ESP_ERR_INVALID_ARG;
    }
    for (size_t i = 0; i < s_screen_count; ++i) {
        if (strcmp(s_screens[i].id, id) == 0) {
            for (size_t j = i + 1; j < s_screen_count; ++j) {
                s_screens[j - 1] = s_screens[j];
            }
            memset(&s_screens[s_screen_count - 1], 0, sizeof(s_screens[0]));
            --s_screen_count;
            return show_model_save_screens();
        }
    }
    return ESP_ERR_NOT_FOUND;
}

esp_err_t show_model_delete_playlist(const char *id)
{
    if (id == NULL || id[0] == '\0') {
        return ESP_ERR_INVALID_ARG;
    }
    for (size_t i = 0; i < s_playlist_count; ++i) {
        if (strcmp(s_playlists[i].id, id) == 0) {
            bool was_default = s_playlists[i].is_default_idle;
            for (size_t j = i + 1; j < s_playlist_count; ++j) {
                s_playlists[j - 1] = s_playlists[j];
            }
            memset(&s_playlists[s_playlist_count - 1], 0, sizeof(s_playlists[0]));
            --s_playlist_count;
            if (was_default && s_playlist_count > 0) {
                s_playlists[0].is_default_idle = true;
            }
            return show_model_save_playlists();
        }
    }
    return ESP_ERR_NOT_FOUND;
}

esp_err_t show_model_export_json(char *screens_json, size_t screens_size, char *playlists_json, size_t playlists_size)
{
    if (screens_json == NULL || playlists_json == NULL || screens_size == 0 || playlists_size == 0) {
        return ESP_ERR_INVALID_ARG;
    }

    int sc = snprintf(screens_json, screens_size, "[");
    for (size_t i = 0; i < s_screen_count && (size_t) sc < screens_size; ++i) {
        sc += snprintf(
            screens_json + sc,
            screens_size - (size_t) sc,
            "%s{\"id\":\"%s\",\"name\":\"%s\",\"type\":%u,\"duration_ms\":%u,\"hold_ms\":%u,\"enabled\":%s,"
            "\"rich_text\":%s,\"repeat_count\":%u,\"gap_columns\":%u,\"layout\":%u,\"text\":\"%s\",\"bitmap_frames\":%u,\"bitmap\":\"%s\"}",
            i == 0 ? "" : ",",
            s_screens[i].id,
            s_screens[i].name,
            (unsigned) s_screens[i].type,
            (unsigned) s_screens[i].duration_ms,
            (unsigned) s_screens[i].hold_ms,
            s_screens[i].enabled ? "true" : "false",
            s_screens[i].rich_text ? "true" : "false",
            (unsigned) s_screens[i].repeat_count,
            (unsigned) s_screens[i].gap_columns,
            (unsigned) s_screens[i].layout,
            s_screens[i].text,
            (unsigned) s_screens[i].bitmap_frames,
            s_screens[i].bitmap);
    }
    snprintf(screens_json + sc, screens_size - (size_t) sc, "]");

    int pc = snprintf(playlists_json, playlists_size, "[");
    for (size_t i = 0; i < s_playlist_count && (size_t) pc < playlists_size; ++i) {
        pc += snprintf(
            playlists_json + pc,
            playlists_size - (size_t) pc,
            "%s{\"id\":\"%s\",\"name\":\"%s\",\"loop\":%s,\"is_default_idle\":%s,\"items\":[",
            i == 0 ? "" : ",",
            s_playlists[i].id,
            s_playlists[i].name,
            s_playlists[i].loop ? "true" : "false",
            s_playlists[i].is_default_idle ? "true" : "false");
        for (size_t j = 0; j < s_playlists[i].item_count && (size_t) pc < playlists_size; ++j) {
            pc += snprintf(
                playlists_json + pc,
                playlists_size - (size_t) pc,
                "%s{\"screen_id\":\"%s\",\"enabled\":%s,\"repeat_count\":%u}",
                j == 0 ? "" : ",",
                s_playlists[i].items[j].screen_id,
                s_playlists[i].items[j].enabled ? "true" : "false",
                (unsigned) s_playlists[i].items[j].repeat_count);
        }
        pc += snprintf(playlists_json + pc, playlists_size - (size_t) pc, "]}");
    }
    snprintf(playlists_json + pc, playlists_size - (size_t) pc, "]");
    return ESP_OK;
}

esp_err_t show_model_import_json(const char *screens_json, const char *playlists_json)
{
    if (screens_json == NULL || playlists_json == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    memset(s_screens, 0, sizeof(s_screens));
    memset(s_playlists, 0, sizeof(s_playlists));
    load_screens_from_json(screens_json);
    load_playlists_from_json(playlists_json);
    if (s_screen_count == 0 || s_playlist_count == 0) {
        show_model_load_defaults();
    }
    if (show_model_save_screens() != ESP_OK) {
        return ESP_FAIL;
    }
    return show_model_save_playlists();
}
