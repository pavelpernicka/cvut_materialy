#include "engine/queue.h"

#include <string.h>

#include "engine/renderer.h"
#include "esp_check.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "system/logger.h"

#define QUEUE_CAPACITY_MAX 64

static queue_item_t s_items[QUEUE_CAPACITY_MAX];
static size_t s_capacity;
static size_t s_len;
static SemaphoreHandle_t s_mutex;

esp_err_t queue_init(size_t max_items)
{
    s_capacity = max_items > QUEUE_CAPACITY_MAX ? QUEUE_CAPACITY_MAX : max_items;
    s_len = 0;
    s_mutex = xSemaphoreCreateMutex();
    return s_mutex == NULL ? ESP_ERR_NO_MEM : ESP_OK;
}

esp_err_t queue_push(const queue_item_t *item)
{
    if (item == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (xSemaphoreTake(s_mutex, pdMS_TO_TICKS(100)) != pdTRUE) {
        return ESP_ERR_TIMEOUT;
    }
    if (s_len >= s_capacity) {
        xSemaphoreGive(s_mutex);
        return ESP_ERR_NO_MEM;
    }
    s_items[s_len++] = *item;
    logger_event(LOG_CAT_GUEST, "queue push id=%s len=%u", item->id, (unsigned) s_len);
    xSemaphoreGive(s_mutex);
    return ESP_OK;
}

esp_err_t queue_pop(queue_item_t *out_item)
{
    if (out_item == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (xSemaphoreTake(s_mutex, pdMS_TO_TICKS(100)) != pdTRUE) {
        return ESP_ERR_TIMEOUT;
    }
    if (s_len == 0) {
        xSemaphoreGive(s_mutex);
        return ESP_ERR_NOT_FOUND;
    }
    *out_item = s_items[0];
    memmove(&s_items[0], &s_items[1], (s_len - 1) * sizeof(s_items[0]));
    --s_len;
    logger_event(LOG_CAT_ENGINE, "queue pop id=%s len=%u", out_item->id, (unsigned) s_len);
    xSemaphoreGive(s_mutex);
    return ESP_OK;
}

esp_err_t queue_peek(queue_item_t *out_item, size_t index)
{
    if (out_item == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (xSemaphoreTake(s_mutex, pdMS_TO_TICKS(100)) != pdTRUE) {
        return ESP_ERR_TIMEOUT;
    }
    if (index >= s_len) {
        xSemaphoreGive(s_mutex);
        return ESP_ERR_NOT_FOUND;
    }
    *out_item = s_items[index];
    xSemaphoreGive(s_mutex);
    return ESP_OK;
}

esp_err_t queue_remove_by_id(const char *id)
{
    if (id == NULL || id[0] == '\0') {
        return ESP_ERR_INVALID_ARG;
    }
    if (xSemaphoreTake(s_mutex, pdMS_TO_TICKS(100)) != pdTRUE) {
        return ESP_ERR_TIMEOUT;
    }
    for (size_t i = 0; i < s_len; ++i) {
        if (strcmp(s_items[i].id, id) == 0) {
            renderer_free_sequence(&s_items[i].sequence);
            if (i + 1 < s_len) {
                memmove(&s_items[i], &s_items[i + 1], (s_len - i - 1) * sizeof(s_items[0]));
            }
            --s_len;
            memset(&s_items[s_len], 0, sizeof(s_items[0]));
            logger_event(LOG_CAT_SYSTEM, "queue delete id=%s len=%u", id, (unsigned) s_len);
            xSemaphoreGive(s_mutex);
            return ESP_OK;
        }
    }
    xSemaphoreGive(s_mutex);
    return ESP_ERR_NOT_FOUND;
}

esp_err_t queue_move_by_id(const char *id, int direction)
{
    if (id == NULL || id[0] == '\0' || (direction != -1 && direction != 1)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (xSemaphoreTake(s_mutex, pdMS_TO_TICKS(100)) != pdTRUE) {
        return ESP_ERR_TIMEOUT;
    }
    for (size_t i = 0; i < s_len; ++i) {
        if (strcmp(s_items[i].id, id) == 0) {
            size_t target = direction < 0 ? (i == 0 ? 0 : i - 1) : (i + 1 >= s_len ? i : i + 1);
            if (target == i) {
                xSemaphoreGive(s_mutex);
                return ESP_OK;
            }
            queue_item_t tmp = s_items[i];
            s_items[i] = s_items[target];
            s_items[target] = tmp;
            logger_event(LOG_CAT_SYSTEM, "queue move id=%s dir=%d", id, direction);
            xSemaphoreGive(s_mutex);
            return ESP_OK;
        }
    }
    xSemaphoreGive(s_mutex);
    return ESP_ERR_NOT_FOUND;
}

size_t queue_len(void)
{
    size_t len = s_len;
    if (s_mutex != NULL && xSemaphoreTake(s_mutex, pdMS_TO_TICKS(20)) == pdTRUE) {
        len = s_len;
        xSemaphoreGive(s_mutex);
    }
    return len;
}

void queue_clear(void)
{
    if (xSemaphoreTake(s_mutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        for (size_t i = 0; i < s_len; ++i) {
            renderer_free_sequence(&s_items[i].sequence);
        }
        s_len = 0;
        logger_event(LOG_CAT_SYSTEM, "queue cleared");
        xSemaphoreGive(s_mutex);
    }
}
