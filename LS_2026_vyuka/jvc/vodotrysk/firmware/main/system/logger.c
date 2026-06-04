#include "system/logger.h"

#include <inttypes.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

#define LOGGER_MAX_EVENTS 200
#define LOGGER_LOG_PATH "/config/events.log"

typedef struct {
    uint64_t ts_ms;
    log_category_t category;
    char message[120];
} log_event_t;

static SemaphoreHandle_t s_log_mutex;
static log_event_t s_events[LOGGER_MAX_EVENTS];
static size_t s_event_count;

static const char *category_name(log_category_t category)
{
    switch (category) {
        case LOG_CAT_SYSTEM: return "system";
        case LOG_CAT_PUMP: return "pump";
        case LOG_CAT_ENGINE: return "engine";
        case LOG_CAT_GUEST: return "guest";
        case LOG_CAT_SENSOR: return "sensor";
        case LOG_CAT_ERROR: return "error";
        default: return "unknown";
    }
}

void logger_init(void)
{
    esp_log_level_set("*", ESP_LOG_INFO);
    if (s_log_mutex == NULL) {
        s_log_mutex = xSemaphoreCreateMutex();
    }
}

void logger_event(log_category_t category, const char *fmt, ...)
{
    if (fmt == NULL) {
        return;
    }

    char message[120];
    va_list args;
    va_start(args, fmt);
    vsnprintf(message, sizeof(message), fmt, args);
    va_end(args);

    ESP_LOGI("event", "[%s] %s", category_name(category), message);

    if (s_log_mutex != NULL && xSemaphoreTake(s_log_mutex, pdMS_TO_TICKS(20)) == pdTRUE) {
        if (s_event_count >= LOGGER_MAX_EVENTS) {
            memmove(&s_events[0], &s_events[1], (LOGGER_MAX_EVENTS - 1) * sizeof(s_events[0]));
            s_event_count = LOGGER_MAX_EVENTS - 1;
        }
        s_events[s_event_count].ts_ms = (uint64_t) (esp_timer_get_time() / 1000ULL);
        s_events[s_event_count].category = category;
        strlcpy(s_events[s_event_count].message, message, sizeof(s_events[s_event_count].message));
        ++s_event_count;
        xSemaphoreGive(s_log_mutex);
    }

    FILE *f = fopen(LOGGER_LOG_PATH, "a");
    if (f != NULL) {
        fprintf(f, "%" PRIu64 " [%s] %s\n", (uint64_t) (esp_timer_get_time() / 1000ULL), category_name(category), message);
        fclose(f);
    }
}

void logger_clear(void)
{
    if (s_log_mutex != NULL && xSemaphoreTake(s_log_mutex, pdMS_TO_TICKS(50)) == pdTRUE) {
        memset(s_events, 0, sizeof(s_events));
        s_event_count = 0;
        xSemaphoreGive(s_log_mutex);
    }
    remove(LOGGER_LOG_PATH);
}

size_t logger_snapshot_json(char *out, size_t out_size)
{
    if (out == NULL || out_size == 0) {
        return 0;
    }
    size_t cursor = 0;
    cursor += (size_t) snprintf(out + cursor, out_size - cursor, "{\"ok\":true,\"events\":[");
    if (s_log_mutex != NULL && xSemaphoreTake(s_log_mutex, pdMS_TO_TICKS(50)) == pdTRUE) {
        for (size_t i = 0; i < s_event_count && cursor < out_size; ++i) {
            cursor += (size_t) snprintf(out + cursor,
                out_size - cursor,
                "%s{\"ts_ms\":%" PRIu64 ",\"category\":\"%s\",\"message\":\"%s\"}",
                i == 0 ? "" : ",",
                s_events[i].ts_ms,
                category_name(s_events[i].category),
                s_events[i].message);
        }
        xSemaphoreGive(s_log_mutex);
    }
    cursor += (size_t) snprintf(out + cursor, out_size - cursor, "]}");
    return cursor;
}
