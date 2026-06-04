#include "system/storage.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "esp_check.h"
#include "esp_log.h"
#include "esp_spiffs.h"
#include "system/logger.h"

static const char *TAG = "storage";
static const char *BASE_PATH = "/config";
static const char *CONFIG_PATH = "/config/config.json";

esp_err_t storage_init(void)
{
    esp_vfs_spiffs_conf_t conf = {
        .base_path = BASE_PATH,
        .partition_label = "littlefs",
        .max_files = 8,
        .format_if_mount_failed = true,
    };
    esp_err_t err = esp_vfs_spiffs_register(&conf);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to mount config filesystem: %s", esp_err_to_name(err));
        return err;
    }

    size_t total = 0;
    size_t used = 0;
    err = esp_spiffs_info("littlefs", &total, &used);
    if (err == ESP_OK) {
        ESP_LOGI(TAG, "Config FS mounted: used=%u / total=%u bytes", (unsigned) used, (unsigned) total);
        logger_event(LOG_CAT_SYSTEM, "storage mounted used=%u total=%u", (unsigned) used, (unsigned) total);
    }
    return ESP_OK;
}

esp_err_t storage_load_config(app_config_t *out_config)
{
    if (out_config == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    FILE *f = fopen(CONFIG_PATH, "rb");
    if (f == NULL) {
        config_load_defaults(out_config);
        ESP_LOGW(TAG, "No config file found, using defaults");
        logger_event(LOG_CAT_SYSTEM, "config missing, restoring defaults");
        return storage_save_config(out_config);
    }

    if (fseek(f, 0, SEEK_END) != 0) {
        fclose(f);
        return ESP_FAIL;
    }
    long size = ftell(f);
    if (size < 0) {
        fclose(f);
        return ESP_FAIL;
    }
    rewind(f);

    char *json = calloc((size_t) size + 1U, 1U);
    if (json == NULL) {
        fclose(f);
        return ESP_ERR_NO_MEM;
    }
    size_t read_len = fread(json, 1, (size_t) size, f);
    fclose(f);
    json[read_len] = '\0';

    esp_err_t err = config_from_json(json, out_config);
    free(json);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Invalid config JSON, restoring defaults");
        logger_event(LOG_CAT_ERROR, "config invalid, restoring defaults");
        config_load_defaults(out_config);
        return storage_save_config(out_config);
    }
    ESP_LOGI(TAG, "Config loaded from %s", CONFIG_PATH);
    logger_event(LOG_CAT_SYSTEM, "config loaded");
    return ESP_OK;
}

esp_err_t storage_save_config(const app_config_t *config)
{
    if (config == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    char *json = NULL;
    ESP_RETURN_ON_ERROR(config_to_json(config, &json), TAG, "config_to_json failed");

    FILE *f = fopen(CONFIG_PATH, "wb");
    if (f == NULL) {
        free(json);
        return ESP_FAIL;
    }
    size_t len = strlen(json);
    size_t written = fwrite(json, 1, len, f);
    fclose(f);
    free(json);

    if (written != len) {
        return ESP_FAIL;
    }
    ESP_LOGI(TAG, "Config saved to %s", CONFIG_PATH);
    logger_event(LOG_CAT_SYSTEM, "config saved");
    return ESP_OK;
}
