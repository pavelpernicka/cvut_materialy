#include "engine/renderer.h"

#include <ctype.h>
#include <stdlib.h>
#include <string.h>

#include "engine/font5x7.h"
#include "engine/template_fields.h"
#include "system/config.h"

typedef struct {
    water_frame_t *frames;
    size_t count;
    size_t capacity;
} frame_builder_t;

typedef struct {
    const char *start;
    size_t len;
} text_line_t;

static size_t split_text_lines(const char *text, text_line_t *lines, size_t max_lines)
{
    size_t count = 0;
    const char *cursor = text;
    const char *line_start = text;
    while (*cursor != '\0' && count < max_lines) {
        if (*cursor == '\n') {
            lines[count].start = line_start;
            lines[count].len = (size_t) (cursor - line_start);
            ++count;
            line_start = cursor + 1;
        }
        ++cursor;
    }
    if (count < max_lines) {
        lines[count].start = line_start;
        lines[count].len = (size_t) (cursor - line_start);
        ++count;
    }
    return count == 0 ? 1 : count;
}

static size_t text_block_column_count(const char *text, uint8_t font_scale)
{
    text_line_t lines[8];
    size_t line_count = split_text_lines(text, lines, 8);
    size_t max_columns = 1;
    size_t advance = (size_t) font_scale * 6U;
    for (size_t i = 0; i < line_count; ++i) {
        size_t line_columns = lines[i].len == 0 ? 1U : (lines[i].len * advance);
        if (line_columns > max_columns) {
            max_columns = line_columns;
        }
    }
    return max_columns;
}

static uint64_t text_column_to_mask(const char *text, size_t column_index, uint8_t font_scale, uint8_t line_spacing)
{
    uint64_t mask = 0;
    text_line_t lines[8];
    size_t line_count = split_text_lines(text, lines, 8);
    size_t scale = font_scale == 0 ? 1U : (size_t) font_scale;
    size_t vertical_gap = (size_t) line_spacing;
    size_t line_height = 7U * scale;
    size_t block_height = (line_count * line_height) + ((line_count > 1 ? line_count - 1 : 0) * vertical_gap);
    size_t y_offset = block_height >= 64U ? 0U : (64U - block_height) / 2U;
    size_t char_advance = 6U * scale;

    for (size_t line = 0; line < line_count; ++line) {
        if (lines[line].len == 0) {
            continue;
        }
        size_t char_index = column_index / char_advance;
        size_t column_in_char = column_index % char_advance;
        if (char_index >= lines[line].len) {
            continue;
        }
        if (column_in_char >= (5U * scale)) {
            continue;
        }
        uint8_t glyph[5];
        font5x7_get_glyph(lines[line].start[char_index], glyph);
        size_t glyph_col = column_in_char / scale;
        uint8_t column_bits = glyph[glyph_col];
        size_t line_y = y_offset + (line * (line_height + vertical_gap));
        for (size_t row = 0; row < 7U; ++row) {
            if (((column_bits >> row) & 0x01U) == 0) {
                continue;
            }
            for (size_t sy = 0; sy < scale; ++sy) {
                size_t valve = line_y + (row * scale) + sy;
                if (valve < 64U) {
                    mask |= (1ULL << valve);
                }
            }
        }
    }
    return mask;
}

static esp_err_t frame_builder_push(frame_builder_t *builder, uint64_t valves, uint16_t duration_ms)
{
    if (builder->count >= builder->capacity) {
        size_t new_capacity = builder->capacity == 0 ? 64 : builder->capacity * 2;
        water_frame_t *new_frames = realloc(builder->frames, new_capacity * sizeof(water_frame_t));
        if (new_frames == NULL) {
            return ESP_ERR_NO_MEM;
        }
        builder->frames = new_frames;
        builder->capacity = new_capacity;
    }
    builder->frames[builder->count].valves = valves;
    builder->frames[builder->count].duration_ms = duration_ms;
    builder->count++;
    return ESP_OK;
}

static esp_err_t append_blank_columns(frame_builder_t *builder, size_t count, uint16_t duration_ms)
{
    for (size_t i = 0; i < count; ++i) {
        if (frame_builder_push(builder, 0, duration_ms) != ESP_OK) {
            return ESP_ERR_NO_MEM;
        }
    }
    return ESP_OK;
}

static const char *screen_template_text(const screen_model_t *screen)
{
    if (screen->text[0] != '\0') {
        return screen->text;
    }
    switch (screen->type) {
        case SCREEN_CLOCK:
            return "CAS {{time}}";
        case SCREEN_SENSOR:
            return "T {{temp}} [gap=4] H {{humidity}}";
        case SCREEN_TEXT:
        default:
            return "";
    }
}

static esp_err_t append_plain_text(frame_builder_t *builder,
    const char *text,
    uint16_t duration_ms,
    uint16_t gap_ms,
    uint8_t font_scale,
    uint8_t line_spacing)
{
    size_t column_count = text_block_column_count(text, font_scale);
    if (text[0] == '\0') {
        return frame_builder_push(builder, 0, duration_ms);
    }
    for (size_t col = 0; col < column_count; ++col) {
        if (frame_builder_push(builder, text_column_to_mask(text, col, font_scale, line_spacing), duration_ms) != ESP_OK) {
            return ESP_ERR_NO_MEM;
        }
        if (gap_ms > 0 && col + 1 < column_count) {
            if (frame_builder_push(builder, 0, gap_ms) != ESP_OK) {
                return ESP_ERR_NO_MEM;
            }
        }
    }
    return ESP_OK;
}

static esp_err_t render_text_sequence(const screen_model_t *screen, const char *text, rendered_sequence_t *out_sequence)
{
    frame_builder_t builder = {0};
    const engine_config_t *engine = &config_get()->engine;
    uint8_t font_scale = screen->font_scale == 0 ? 1 : screen->font_scale;
    uint8_t line_spacing = screen->line_spacing;
    uint16_t default_duration = (uint16_t) (
        engine->column_period_ms != 0 ? engine->column_period_ms :
        (engine->solenoid_hold_ms != 0 ? engine->solenoid_hold_ms : 35));
    uint16_t gap_duration = (uint16_t) engine->text_column_gap_ms;
    uint16_t current_duration = default_duration;
    size_t leading_blanks = 0;

    if (screen->layout == SCREEN_LAYOUT_CENTER && !screen->rich_text) {
        size_t columns = text_block_column_count(text, font_scale);
        if (columns < 64) {
            leading_blanks = (64 - columns) / 2;
        }
    }

    if (append_blank_columns(&builder, leading_blanks, default_duration) != ESP_OK) {
        goto fail;
    }

    if (!screen->rich_text) {
        if (append_plain_text(&builder, text, default_duration, gap_duration, font_scale, line_spacing) != ESP_OK) {
            goto fail;
        }
    } else {
        const char *cursor = text;
        char plain_segment[192];
        size_t plain_len = 0;

        while (*cursor != '\0') {
            if (*cursor == '[') {
                const char *end = strchr(cursor, ']');
                if (end != NULL) {
                    if (plain_len > 0) {
                        plain_segment[plain_len] = '\0';
                        if (append_plain_text(&builder, plain_segment, current_duration, gap_duration, font_scale, line_spacing) != ESP_OK) {
                            goto fail;
                        }
                        plain_len = 0;
                    }
                    if (strncmp(cursor, "[gap=", 5) == 0) {
                        size_t gap = (size_t) atoi(cursor + 5);
                        if (append_blank_columns(&builder, gap, current_duration) != ESP_OK) {
                            goto fail;
                        }
                    } else if (strncmp(cursor, "[pause=", 7) == 0) {
                        uint16_t pause_ms = (uint16_t) atoi(cursor + 7);
                        if (frame_builder_push(&builder, 0, pause_ms == 0 ? current_duration : pause_ms) != ESP_OK) {
                            goto fail;
                        }
                    } else if (strncmp(cursor, "[speed=", 7) == 0) {
                        current_duration = (uint16_t) atoi(cursor + 7);
                        if (current_duration == 0) {
                            current_duration = default_duration;
                        }
                    } else if (strncmp(cursor, "[reset]", 7) == 0 || strncmp(cursor, "[/speed]", 8) == 0) {
                        current_duration = default_duration;
                    }
                    cursor = end + 1;
                    continue;
                }
            }
            if (plain_len + 1 < sizeof(plain_segment)) {
                plain_segment[plain_len++] = *cursor;
            }
            ++cursor;
        }
        if (plain_len > 0) {
            plain_segment[plain_len] = '\0';
            if (append_plain_text(&builder, plain_segment, current_duration, gap_duration, font_scale, line_spacing) != ESP_OK) {
                goto fail;
            }
        }
    }

    if (screen->layout == SCREEN_LAYOUT_STATIC && builder.count > 64) {
        builder.count = 64;
    } else if (screen->layout == SCREEN_LAYOUT_CENTER && builder.count < 64) {
        if (append_blank_columns(&builder, 64 - builder.count, default_duration) != ESP_OK) {
            goto fail;
        }
    } else if (screen->layout == SCREEN_LAYOUT_SCROLL) {
        size_t gap = screen->gap_columns == 0 ? 6 : screen->gap_columns;
        if (append_blank_columns(&builder, gap, default_duration) != ESP_OK) {
            goto fail;
        }
    }

    for (uint8_t i = 1; i < (screen->repeat_count == 0 ? 1 : screen->repeat_count); ++i) {
        size_t initial_count = builder.count;
        for (size_t j = 0; j < initial_count; ++j) {
            if (frame_builder_push(&builder, builder.frames[j].valves, builder.frames[j].duration_ms) != ESP_OK) {
                goto fail;
            }
        }
    }

    out_sequence->frames = builder.frames;
    out_sequence->frame_count = builder.count;
    out_sequence->owns_memory = true;
    return ESP_OK;

fail:
    free(builder.frames);
    return ESP_ERR_NO_MEM;
}

static esp_err_t render_test_sequence(const screen_model_t *screen, rendered_sequence_t *out_sequence)
{
    frame_builder_t builder = {0};
    uint16_t duration_ms = (uint16_t) (screen->duration_ms == 0 ? 35 : screen->duration_ms);
    for (size_t i = 0; i < 64; ++i) {
        if (frame_builder_push(&builder, 1ULL << i, duration_ms) != ESP_OK) {
            free(builder.frames);
            return ESP_ERR_NO_MEM;
        }
    }
    out_sequence->frames = builder.frames;
    out_sequence->frame_count = builder.count;
    out_sequence->owns_memory = true;
    return ESP_OK;
}

static esp_err_t render_bitmap_sequence(const screen_model_t *screen, rendered_sequence_t *out_sequence)
{
    if (screen->bitmap_frames == 0 || screen->bitmap[0] == '\0') {
        return ESP_ERR_INVALID_ARG;
    }
    frame_builder_t builder = {0};
    const engine_config_t *engine = &config_get()->engine;
    uint16_t duration_ms = (uint16_t) (engine->solenoid_hold_ms == 0 ? 35 : engine->solenoid_hold_ms);
    uint16_t gap_ms = (uint16_t) engine->bitmap_row_gap_ms;
    size_t frame_count = screen->bitmap_frames > SCREEN_BITMAP_MAX_FRAMES ? SCREEN_BITMAP_MAX_FRAMES : screen->bitmap_frames;
    for (size_t i = 0; i < frame_count; ++i) {
        char hex[17];
        memcpy(hex, &screen->bitmap[i * 16U], 16U);
        hex[16] = '\0';
        if (frame_builder_push(&builder, strtoull(hex, NULL, 16), duration_ms) != ESP_OK) {
            free(builder.frames);
            return ESP_ERR_NO_MEM;
        }
        if (gap_ms > 0 && i + 1 < frame_count) {
            if (frame_builder_push(&builder, 0, gap_ms) != ESP_OK) {
                free(builder.frames);
                return ESP_ERR_NO_MEM;
            }
        }
    }
    if (screen->hold_ms > 0 && builder.count > 0) {
        if (frame_builder_push(&builder, builder.frames[builder.count - 1].valves, (uint16_t) screen->hold_ms) != ESP_OK) {
            free(builder.frames);
            return ESP_ERR_NO_MEM;
        }
    }
    out_sequence->frames = builder.frames;
    out_sequence->frame_count = builder.count;
    out_sequence->owns_memory = true;
    return ESP_OK;
}

esp_err_t renderer_render_screen(const screen_model_t *screen, rendered_sequence_t *out_sequence)
{
    if (screen == NULL || out_sequence == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    memset(out_sequence, 0, sizeof(*out_sequence));

    if (screen->type == SCREEN_TEST) {
        return render_test_sequence(screen, out_sequence);
    }
    if (screen->type == SCREEN_BITMAP) {
        return render_bitmap_sequence(screen, out_sequence);
    }

    char rendered[192];
    if (template_fields_render(screen_template_text(screen), rendered, sizeof(rendered)) != ESP_OK) {
        return ESP_FAIL;
    }
    return render_text_sequence(screen, rendered, out_sequence);
}

void renderer_free_sequence(rendered_sequence_t *sequence)
{
    if (sequence != NULL && sequence->owns_memory && sequence->frames != NULL) {
        free(sequence->frames);
        sequence->frames = NULL;
        sequence->frame_count = 0;
        sequence->owns_memory = false;
    }
}
