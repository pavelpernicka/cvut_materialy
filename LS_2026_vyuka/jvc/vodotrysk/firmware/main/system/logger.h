#pragma once

#include <stddef.h>

typedef enum {
    LOG_CAT_SYSTEM = 0,
    LOG_CAT_PUMP,
    LOG_CAT_ENGINE,
    LOG_CAT_GUEST,
    LOG_CAT_SENSOR,
    LOG_CAT_ERROR,
} log_category_t;

void logger_init(void);
void logger_event(log_category_t category, const char *fmt, ...);
void logger_clear(void);
size_t logger_snapshot_json(char *out, size_t out_size);
