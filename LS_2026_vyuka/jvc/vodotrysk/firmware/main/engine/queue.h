#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "engine/water_engine.h"
#include "esp_err.h"

typedef struct {
    char id[32];
    char source_ip[48];
    char author[32];
    uint8_t priority;
    uint64_t created_ms;
    uint32_t estimated_duration_ms;
    rendered_sequence_t sequence;
} queue_item_t;

esp_err_t queue_init(size_t max_items);
esp_err_t queue_push(const queue_item_t *item);
esp_err_t queue_pop(queue_item_t *out_item);
esp_err_t queue_peek(queue_item_t *out_item, size_t index);
esp_err_t queue_remove_by_id(const char *id);
esp_err_t queue_move_by_id(const char *id, int direction);
size_t queue_len(void);
void queue_clear(void);
