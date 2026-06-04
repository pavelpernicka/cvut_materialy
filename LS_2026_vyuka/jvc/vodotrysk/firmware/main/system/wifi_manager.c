#include "system/wifi_manager.h"

#include <stdio.h>
#include <string.h>

#include "esp_event.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "lwip/inet.h"
#include "nvs_flash.h"
#include "system/config.h"

static const char *TAG = "wifi_manager";
static char s_mode[16] = "ap";
static char s_ip[16] = "0.0.0.0";
static char s_ssid[32];
static esp_netif_t *s_ap_netif;
static esp_netif_t *s_sta_netif;
static bool s_sta_has_ip;
static bool s_ap_active;
static bool s_fallback_ap;
static int8_t s_rssi = -127;

static esp_err_t wifi_manager_start_internal(const wifi_config_model_t *cfg);

static void update_ip_string(esp_netif_t *netif)
{
    if (netif == NULL) {
        return;
    }
    esp_netif_ip_info_t ip_info;
    if (esp_netif_get_ip_info(netif, &ip_info) == ESP_OK) {
        snprintf(s_ip, sizeof(s_ip), IPSTR, IP2STR(&ip_info.ip));
    }
}

static void wifi_event_handler(void *arg, esp_event_base_t event_base, int32_t event_id, void *event_data)
{
    (void) arg;
    (void) event_data;

    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        s_sta_has_ip = false;
        s_rssi = -127;
        if (s_ap_netif != NULL) {
            update_ip_string(s_ap_netif);
        }
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_AP_START) {
        s_ap_active = true;
        if (!s_sta_has_ip && s_ap_netif != NULL) {
            update_ip_string(s_ap_netif);
        }
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_AP_STOP) {
        s_ap_active = false;
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        s_sta_has_ip = true;
        update_ip_string(s_sta_netif);
        wifi_ap_record_t ap_info;
        if (esp_wifi_sta_get_ap_info(&ap_info) == ESP_OK) {
            s_rssi = ap_info.rssi;
            strlcpy(s_ssid, (const char *) ap_info.ssid, sizeof(s_ssid));
        }
    }
}

static void fill_default_ssid(char *out, size_t out_size)
{
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_SOFTAP);
    snprintf(out, out_size, "water-curtain-%02X%02X", mac[4], mac[5]);
}

static esp_err_t configure_ap(const wifi_config_model_t *wifi_cfg)
{
    wifi_config_t ap_cfg = {0};
    if (wifi_cfg->ap_ssid[0] != '\0') {
        strlcpy((char *) ap_cfg.ap.ssid, wifi_cfg->ap_ssid, sizeof(ap_cfg.ap.ssid));
    } else {
        fill_default_ssid((char *) ap_cfg.ap.ssid, sizeof(ap_cfg.ap.ssid));
    }
    strlcpy((char *) ap_cfg.ap.password, wifi_cfg->ap_password, sizeof(ap_cfg.ap.password));
    ap_cfg.ap.ssid_len = strlen((char *) ap_cfg.ap.ssid);
    ap_cfg.ap.channel = 1;
    ap_cfg.ap.max_connection = 4;
    ap_cfg.ap.authmode = strlen((char *) ap_cfg.ap.password) >= 8 ? WIFI_AUTH_WPA2_PSK : WIFI_AUTH_OPEN;
    if (ap_cfg.ap.authmode == WIFI_AUTH_OPEN) {
        ap_cfg.ap.password[0] = '\0';
    }
    return esp_wifi_set_config(WIFI_IF_AP, &ap_cfg);
}

static esp_err_t configure_sta(const wifi_config_model_t *wifi_cfg)
{
    wifi_config_t sta_cfg = {0};
    strlcpy((char *) sta_cfg.sta.ssid, wifi_cfg->client_ssid, sizeof(sta_cfg.sta.ssid));
    strlcpy((char *) sta_cfg.sta.password, wifi_cfg->client_password, sizeof(sta_cfg.sta.password));
    sta_cfg.sta.threshold.authmode = WIFI_AUTH_OPEN;
    sta_cfg.sta.pmf_cfg.capable = true;
    sta_cfg.sta.pmf_cfg.required = false;
    return esp_wifi_set_config(WIFI_IF_STA, &sta_cfg);
}

static esp_err_t wifi_manager_start_internal(const wifi_config_model_t *cfg)
{
    bool want_sta = strcmp(cfg->mode, "client") == 0 || strcmp(cfg->mode, "ap_client") == 0;
    bool want_ap = strcmp(cfg->mode, "ap") == 0 || strcmp(cfg->mode, "ap_client") == 0 ||
                   (strcmp(cfg->mode, "client") == 0 && cfg->fallback_ap);
    s_fallback_ap = cfg->fallback_ap;
    s_sta_has_ip = false;
    s_ap_active = want_ap;
    s_rssi = -127;
    s_ssid[0] = '\0';

    if (want_ap) {
        if (s_ap_netif == NULL) {
            s_ap_netif = esp_netif_create_default_wifi_ap();
        }
    }
    if (want_sta) {
        if (s_sta_netif == NULL) {
            s_sta_netif = esp_netif_create_default_wifi_sta();
        }
    }

    wifi_mode_t mode = WIFI_MODE_NULL;
    if (want_ap && want_sta) {
        mode = WIFI_MODE_APSTA;
        strlcpy(s_mode, "ap_client", sizeof(s_mode));
    } else if (want_sta) {
        mode = WIFI_MODE_STA;
        strlcpy(s_mode, "client", sizeof(s_mode));
    } else {
        mode = WIFI_MODE_AP;
        strlcpy(s_mode, "ap", sizeof(s_mode));
    }

    ESP_RETURN_ON_ERROR(esp_wifi_set_mode(mode), TAG, "set mode failed");
    if (want_ap) {
        ESP_RETURN_ON_ERROR(configure_ap(cfg), TAG, "configure ap failed");
    }
    if (want_sta) {
        ESP_RETURN_ON_ERROR(configure_sta(cfg), TAG, "configure sta failed");
    } else {
        s_ssid[0] = '\0';
    }

    ESP_RETURN_ON_ERROR(esp_wifi_start(), TAG, "wifi start failed");
    if (want_ap && s_ap_netif != NULL) {
        update_ip_string(s_ap_netif);
    }

    ESP_LOGI(TAG, "Wi-Fi started in mode=%s ip=%s", s_mode, s_ip);
    return ESP_OK;
}

esp_err_t wifi_manager_init(void)
{
    const app_config_t *cfg = config_get();

    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(err);
    ESP_ERROR_CHECK(esp_netif_init());
    err = esp_event_loop_create_default();
    if (err != ESP_OK && err != ESP_ERR_INVALID_STATE) {
        ESP_ERROR_CHECK(err);
    }

    wifi_init_config_t wifi_init = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&wifi_init));
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &wifi_event_handler, NULL));
    ESP_ERROR_CHECK(esp_wifi_set_storage(WIFI_STORAGE_RAM));
    return wifi_manager_start_internal(&cfg->wifi);
}

esp_err_t wifi_manager_apply_config(const wifi_config_model_t *cfg)
{
    if (cfg == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    (void) esp_wifi_stop();
    return wifi_manager_start_internal(cfg);
}

esp_err_t wifi_manager_reconnect(void)
{
    esp_err_t err = esp_wifi_disconnect();
    if (err != ESP_OK && err != ESP_ERR_WIFI_NOT_CONNECT) {
        return err;
    }
    return esp_wifi_connect();
}

wifi_status_t wifi_manager_get_status(void)
{
    wifi_status_t status = {0};
    strlcpy(status.mode, s_mode, sizeof(status.mode));
    strlcpy(status.ip, s_ip, sizeof(status.ip));
    strlcpy(status.ssid, s_ssid, sizeof(status.ssid));
    status.rssi = s_rssi;
    status.sta_has_ip = s_sta_has_ip;
    status.ap_active = s_ap_active;
    status.fallback_ap = s_fallback_ap;
    return status;
}

const char *wifi_manager_get_ip(void)
{
    return s_ip;
}

const char *wifi_manager_get_mode(void)
{
    return s_mode;
}
