#include "network_manager.h"
#include "alert_store.h"
#include "api_client.h"
#include "config.h"
#include "gsm_link.h"
#include <Preferences.h>
#include <WiFi.h>
#include <string>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include <freertos/semphr.h>
#include <freertos/task.h>
#if __has_include("secrets.h")
#include "secrets.h"
#endif
#ifndef RESQ_WIFI_SSID
#define RESQ_WIFI_SSID ""
#define RESQ_WIFI_PASSWORD ""
#endif

// ---- NVS adapter for AlertStore ------------------------------------------------
struct NvsStorage {
  Preferences p;
  void begin() { p.begin("resq-alerts", false); }
  uint32_t getU(const char* k) { return p.getUInt(k, 0); }
  void putU(const char* k, uint32_t v) { p.putUInt(k, v); }
  std::string getS(const std::string& k) { return std::string(p.getString(k.c_str(), "").c_str()); }
  void putS(const std::string& k, const std::string& v) { p.putString(k.c_str(), v.c_str()); }
  void remove(const std::string& k) { p.remove(k.c_str()); }
};

static constexpr size_t BODY_MAX = 1200;
struct TelemetryJob { char body[BODY_MAX]; };

static NvsStorage nvs;
static AlertStore<NvsStorage>* alerts = nullptr;
static SemaphoreHandle_t alertLock = nullptr;
static QueueHandle_t telemetryQ = nullptr;
static ApiClient client;
static uint32_t bootCount = 0, seq = 0;
static bool taskStarted = false;

void NetworkManager::begin() {
  Preferences meta; meta.begin("resq-meta", false);
  bootCount = meta.getUInt("boot", 0) + 1; meta.putUInt("boot", bootCount); meta.end();
  nvs.begin();
  alerts = new AlertStore<NvsStorage>(nvs, PERSISTENT_ALERT_SLOTS);
  alertLock = xSemaphoreCreateMutex();
  telemetryQ = xQueueCreate(OFFLINE_QUEUE_CAPACITY - 2, sizeof(TelemetryJob));
  Serial.printf("[INIT] boot=%lu pending alerts from previous run=%lu\n", (unsigned long)bootCount, (unsigned long)alerts->size());
  WiFi.mode(WIFI_STA); WiFi.setAutoReconnect(false);
  if (!strlen(RESQ_WIFI_SSID)) Serial.println("[WARN] Wi-Fi credentials missing");
  if (!client.configured()) Serial.println("[WARN] backend URL missing; events stay queued on the device");
  if (!hasConfiguredLocation()) Serial.println("[INFO] no fixed coordinates in firmware; backend must have this device's location registered");
  GsmLink::begin();
  taskStarted = xTaskCreatePinnedToCore(taskEntry, "resq-network", 10240, nullptr, 1, nullptr, 0) == pdPASS;
  if (!taskStarted) Serial.println("[ERROR] network task allocation failed; sensor sampling continues");
}

uint32_t NetworkManager::pendingAlerts() {
  if (!alerts) return 0;
  xSemaphoreTake(alertLock, portMAX_DELAY); uint32_t n = alerts->size(); xSemaphoreGive(alertLock); return n;
}

bool NetworkManager::enqueue(const SensorReadings& r, const HazardAssessment& h) {
  if (!taskStarted) return false;
  if (SIMULATION_MODE && !ALLOW_SIMULATION_UPLOAD) return true;
  char eventId[64]; formatEventId(eventId, sizeof eventId, DEVICE_ID, bootCount, ++seq);
  const String body = client.buildPayload(r, h, eventId, WiFi.status() == WL_CONNECTED, millis());
  if (h.newAlert) {
    xSemaphoreTake(alertLock, portMAX_DELAY);
    const bool ok = alerts->push(std::string(body.c_str()));
    xSemaphoreGive(alertLock);
    Serial.printf("[QUEUE] alert %s stored in flash%s\n", eventId, ok ? "" : " (oldest pending alert overwritten: store full)");
    return true;
  }
  if (body.length() >= BODY_MAX) return false;
  TelemetryJob j; strncpy(j.body, body.c_str(), BODY_MAX); j.body[BODY_MAX - 1] = 0;
  if (xQueueSend(telemetryQ, &j, 0) != pdTRUE) {  // drop oldest telemetry to keep the newest
    TelemetryJob old; xQueueReceive(telemetryQ, &old, 0); xQueueSend(telemetryQ, &j, 0);
  }
  return true;
}

void NetworkManager::taskEntry(void*) { static NetworkManager n; n.run(); }

void NetworkManager::run() {
  uint32_t wifiRetry = WIFI_RETRY_BASE_MS, nextWifi = 0, backoff = 1000, nextSend = 0;
  bool wasConnected = false;
  for (;;) {
    const uint32_t now = millis();
    if (strlen(RESQ_WIFI_SSID) && WiFi.status() != WL_CONNECTED && (int32_t)(now - nextWifi) >= 0) {
      WiFi.begin(RESQ_WIFI_SSID, RESQ_WIFI_PASSWORD);
      nextWifi = now + wifiRetry; wifiRetry = min<uint32_t>(wifiRetry * 2, WIFI_RETRY_MAX_MS);
      Serial.println("[WIFI] connection attempt");
    }
    const bool wifi = WiFi.status() == WL_CONNECTED;
    if (wifi && !wasConnected) { Serial.printf("[WIFI] connected IP=%s\n", WiFi.localIP().toString().c_str()); wifiRetry = WIFI_RETRY_BASE_MS; }
    if (!wifi && wasConnected) Serial.println("[WARN] Wi-Fi lost; queued events retained");
    wasConnected = wifi;

    if ((int32_t)(now - nextSend) >= 0 && client.configured()) {
      bool sent = false, attempted = false;
      std::string alert;
      xSemaphoreTake(alertLock, portMAX_DELAY); const bool haveAlert = alerts->peek(alert); xSemaphoreGive(alertLock);
      if (haveAlert) {
        attempted = true;
        String body(alert.c_str());
        sent = (wifi && client.sendWifi(body)) || (!wifi && client.sendGprs(body));
        if (sent) { xSemaphoreTake(alertLock, portMAX_DELAY); alerts->pop(); xSemaphoreGive(alertLock); }
      } else if (wifi) {  // telemetry only over Wi-Fi (GPRS data is reserved for alerts)
        TelemetryJob j;
        if (xQueuePeek(telemetryQ, &j, 0) == pdTRUE) {
          attempted = true;
          sent = client.sendWifi(String(j.body));
          if (sent) xQueueReceive(telemetryQ, &j, 0);
        }
      }
      if (attempted) {
        if (sent) { backoff = 1000; nextSend = now + API_MIN_INTERVAL_MS; }
        else { nextSend = now + backoff; backoff = min<uint32_t>(backoff * 2, 60000); }  // bounded exponential retry
      }
    }
    vTaskDelay(pdMS_TO_TICKS(100));
  }
}
