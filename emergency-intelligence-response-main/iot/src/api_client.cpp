#include "api_client.h"
#include "config.h"
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#if __has_include("secrets.h")
#include "secrets.h"
#else
#define RESQ_WIFI_SSID ""
#define RESQ_WIFI_PASSWORD ""
#define RESQ_API_BASE_URL ""
#define RESQ_DEVICE_TOKEN ""
#define RESQ_ROOT_CA ""
#endif
bool ApiClient::configured() const {return strlen(RESQ_API_BASE_URL)>0;}
bool ApiClient::post(const SensorReadings& r,const HazardAssessment& h,bool wifi,uint32_t uptime){
  if(!wifi||!configured())return false;
  if(SIMULATION_MODE&&!ALLOW_SIMULATION_UPLOAD){Serial.println("[SIM] simulated sample kept local; API upload disabled");return true;}
  const String base=RESQ_API_BASE_URL; const bool https=base.startsWith("https://");
  if(!https&&!(ALLOW_INSECURE_LOCAL_HTTP&&(base.startsWith("http://127.0.0.1")||base.startsWith("http://localhost")||base.startsWith("http://10.")||base.startsWith("http://192.168.")||base.startsWith("http://172.")))){Serial.println("[ERROR] refusing insecure non-local API URL");return false;}
  JsonDocument d; d["device_id"]=DEVICE_ID;d["event_type"]=h.newAlert?h.eventType:"TELEMETRY";
  d["firmware_version"]=FIRMWARE_VERSION;d["wifi_connected"]=wifi;d["uptime_ms"]=uptime;
  d["mpu6050_available"]=r.mpuAvailable;d["dht22_available"]=r.dhtValid;
  d["mq2_available"]=r.mq2Available;d["mq2_warmed"]=r.mq2Warmed;d["mq2_calibrated"]=r.mq2Calibrated;
  if(r.simulated)d["simulation"]=true;
  if(r.dhtValid){d["temperature"]=r.temperatureC;d["humidity_percent"]=r.humidityPercent;}
  // Backend's smoke_level means ppm. This firmware has no calibrated ppm conversion; omit it.
  if(r.accelerationMagnitudeG==r.accelerationMagnitudeG)d["acceleration_magnitude_g"]=r.accelerationMagnitudeG;
  if(r.accelerationMagnitudeMps2==r.accelerationMagnitudeMps2)d["acceleration_magnitude_mps2"]=r.accelerationMagnitudeMps2;
  if(r.dynamicAccelerationG==r.dynamicAccelerationG)d["dynamic_acceleration_g"]=r.dynamicAccelerationG;
  if(r.vibrationRmsG==r.vibrationRmsG)d["vibration_rms_g"]=r.vibrationRmsG;
  if(r.gxDps==r.gxDps)d["gyro_x_dps"]=r.gxDps;
  if(r.gyDps==r.gyDps)d["gyro_y_dps"]=r.gyDps;
  if(r.gzDps==r.gzDps)d["gyro_z_dps"]=r.gzDps;
  if(r.mq2Available){d["mq2_raw_adc"]=r.mq2RawAdc;d["mq2_filtered_adc"]=r.mq2FilteredAdc;if(r.mq2Calibrated)d["mq2_baseline_adc"]=r.mq2BaselineAdc;}
  d["alert_qualified"]=h.newAlert;
  d["simulated"]=r.simulated;
  d["hazard_severity"]=severityName(h.severity);
  if(h.newAlert){d["source_sensor"]=h.sourceSensor;d["observed_value"]=h.observedValue;d["threshold_value"]=h.thresholdValue;d["measurement_unit"]=h.unit;d["reason"]=h.reason;}
  // The legacy `impact` field is an incident trigger; send it only for a qualified motion alert.
  if(h.newAlert&&String(h.eventType)=="ACCIDENT"&&r.accelerationMagnitudeG==r.accelerationMagnitudeG)d["impact"]=r.accelerationMagnitudeG;
  if(!hasConfiguredLocation()){Serial.println("[WARN] event withheld: backend requires genuine configured latitude/longitude");return false;}
  d["latitude"]=FIXED_LATITUDE;d["longitude"]=FIXED_LONGITUDE; String body;serializeJson(d,body);
  HTTPClient http; WiFiClient plain; WiFiClientSecure secure;
  if(https){if(strlen(RESQ_ROOT_CA)==0){Serial.println("[ERROR] HTTPS requires a configured root CA; refusing insecure TLS");return false;}secure.setCACert(RESQ_ROOT_CA);if(!http.begin(secure,base+"/api/v1/iot/events"))return false;}
  else if(!http.begin(plain,base+"/api/v1/iot/events"))return false;
  http.setConnectTimeout(HTTP_TIMEOUT_MS);http.setTimeout(HTTP_TIMEOUT_MS);http.addHeader("Content-Type","application/json");
  if(strlen(RESQ_DEVICE_TOKEN))http.addHeader("Authorization",String("Bearer ")+RESQ_DEVICE_TOKEN);
  const int code=http.POST(body);const String response=code>0?http.getString():"";http.end();
  if(code>=200&&code<300){JsonDocument ack;if(deserializeJson(ack,response)||ack["reading_id"].isNull()){Serial.printf("[API] unexpected acknowledgement HTTP=%d\n",code);return false;}Serial.printf("[API] accepted reading=%s incident=%s uptime=%lu\n",ack["reading_id"]|"?",ack["incident_id"]|"none",(unsigned long)uptime);return true;}
  Serial.printf("[API] request failed HTTP=%d\n",code);return false;
}
