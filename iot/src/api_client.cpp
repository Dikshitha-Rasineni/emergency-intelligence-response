#include "api_client.h"
#include "config.h"
#include "gsm_link.h"
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#if __has_include("secrets.h")
#include "secrets.h"
#endif
#ifndef RESQ_API_BASE_URL
#define RESQ_WIFI_SSID ""
#define RESQ_WIFI_PASSWORD ""
#define RESQ_API_BASE_URL ""
#define RESQ_DEVICE_TOKEN ""
#define RESQ_ROOT_CA ""
#endif

bool ApiClient::configured() const { return strlen(RESQ_API_BASE_URL) > 0; }

static bool isLocalHttp(const String& b) {
  return b.startsWith("http://127.0.0.1") || b.startsWith("http://localhost") || b.startsWith("http://10.") ||
         b.startsWith("http://192.168.") || b.startsWith("http://172.");
}

String ApiClient::buildPayload(const SensorReadings& r, const HazardAssessment& h, const char* eventId, bool wifi, uint32_t uptime) const {
  JsonDocument d;
  d["device_id"] = DEVICE_ID; d["event_id"] = eventId; d["event_type"] = h.newAlert ? h.eventType : "TELEMETRY";
  d["firmware_version"] = FIRMWARE_VERSION; d["wifi_connected"] = wifi; d["uptime_ms"] = uptime;
  d["mpu6050_available"] = r.mpuAvailable; d["dht22_available"] = r.dhtValid;
  d["mq2_available"] = r.mq2Available; d["mq2_warmed"] = r.mq2Warmed; d["mq2_calibrated"] = r.mq2Calibrated;
  if (r.dhtValid) { d["temperature"] = r.temperatureC; d["humidity_percent"] = r.humidityPercent; }
  if (isfinite(r.accelerationMagnitudeG)) d["acceleration_magnitude_g"] = r.accelerationMagnitudeG;
  if (isfinite(r.accelerationMagnitudeMps2)) d["acceleration_magnitude_mps2"] = r.accelerationMagnitudeMps2;
  if (isfinite(r.dynamicAccelerationG)) d["dynamic_acceleration_g"] = r.dynamicAccelerationG;
  if (isfinite(r.vibrationRmsG)) d["vibration_rms_g"] = r.vibrationRmsG;
  if (isfinite(r.gxDps)) { d["gyro_x_dps"] = r.gxDps; d["gyro_y_dps"] = r.gyDps; d["gyro_z_dps"] = r.gzDps; }
  if (r.mq2Available) { d["mq2_raw_adc"] = r.mq2RawAdc; d["mq2_filtered_adc"] = r.mq2FilteredAdc; if (r.mq2Calibrated) d["mq2_baseline_adc"] = r.mq2BaselineAdc; }
  if (r.waterAvailable) d["water_level_raw_adc"] = r.waterRawAdc;
  if (r.fsrAvailable) d["fsr_raw_adc"] = r.fsrRawAdc;
  d["alert_qualified"] = h.newAlert; d["simulated"] = r.simulated; d["hazard_severity"] = severityName(h.severity);
  if (h.newAlert) { d["source_sensor"] = h.sourceSensor; d["observed_value"] = h.observedValue; d["threshold_value"] = h.thresholdValue;
                    d["measurement_unit"] = h.unit; d["reason"] = h.reason; }
  if (h.newAlert && String(h.eventType) == "ACCIDENT" && isfinite(r.accelerationMagnitudeG)) d["impact"] = r.accelerationMagnitudeG;
  // Location: only a real configured installation point. Otherwise omit; the backend then uses the
  // location registered for this device by an administrator, or rejects the alert as unlocated.
  if (hasConfiguredLocation()) { d["latitude"] = FIXED_LATITUDE; d["longitude"] = FIXED_LONGITUDE; }
  String body; serializeJson(d, body); return body;
}

static String withTransport(const String& body, const char* transport) {
  JsonDocument d; if (deserializeJson(d, body)) return body;
  d["transport"] = transport; String out; serializeJson(d, out); return out;
}

static bool acknowledged(int code, const String& response) {
  if (code < 200 || code >= 300) return false;
  JsonDocument ack;
  if (deserializeJson(ack, response) || ack["reading_id"].isNull()) { Serial.printf("[API] unexpected acknowledgement HTTP=%d\n", code); return false; }
  Serial.printf("[API] ack status=%s reading=%s incident=%s\n", ack["status"] | "?", ack["reading_id"] | "?", ack["incident_id"] | "none");
  return true;
}

bool ApiClient::sendWifi(const String& raw) {
  if (!configured() || WiFi.status() != WL_CONNECTED) return false;
  const String base = RESQ_API_BASE_URL; const bool https = base.startsWith("https://");
  if (!https && !(ALLOW_INSECURE_LOCAL_HTTP && isLocalHttp(base))) { Serial.println("[ERROR] refusing insecure non-local API URL"); return false; }
  HTTPClient http; WiFiClient plain; WiFiClientSecure secure;
  if (https) {
    if (strlen(RESQ_ROOT_CA) == 0) { Serial.println("[ERROR] HTTPS requires a configured root CA"); return false; }
    secure.setCACert(RESQ_ROOT_CA);
    if (!http.begin(secure, base + "/api/v1/iot/events")) return false;
  } else if (!http.begin(plain, base + "/api/v1/iot/events")) return false;
  http.setConnectTimeout(HTTP_TIMEOUT_MS); http.setTimeout(HTTP_TIMEOUT_MS);
  http.addHeader("Content-Type", "application/json");
  if (strlen(RESQ_DEVICE_TOKEN)) http.addHeader("Authorization", String("Bearer ") + RESQ_DEVICE_TOKEN);
  const int code = http.POST(withTransport(raw, "WIFI"));
  const String response = code > 0 ? http.getString() : "";
  http.end();
  if (!acknowledged(code, response)) { Serial.printf("[API] Wi-Fi delivery failed HTTP=%d\n", code); return false; }
  return true;
}

bool ApiClient::sendGprs(const String& raw) {
  if (!ENABLE_SIM800L || !GPRS_ALLOW_PLAINTEXT) return false;
  int code = 0; String response;
  if (!GsmLink::post(withTransport(raw, "GPRS"), code, response)) return false;
  if (!acknowledged(code, response)) { Serial.printf("[GPRS] delivery failed HTTP=%d\n", code); return false; }
  return true;
}
