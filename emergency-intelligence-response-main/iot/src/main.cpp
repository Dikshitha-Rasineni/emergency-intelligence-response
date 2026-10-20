#include <Arduino.h>
#include <WiFi.h>
#include "config.h"
#include "sensor_manager.h"
#include "hazard_detector.h"
#include "network_manager.h"

static SensorManager sensors; static HazardDetector hazards; static NetworkManager network;
static uint32_t lastTelemetry=0,lastSummary=0;
void setup(){
  Serial.begin(SERIAL_BAUD);delay(100);
  Serial.printf("RESQ.AI firmware=%s device=%s\n",FIRMWARE_VERSION,DEVICE_ID);
  Serial.printf("[CFG] sampling=%lums telemetry=%lums simulation=%s\n",(unsigned long)SENSOR_TICK_MS,(unsigned long)TELEMETRY_INTERVAL_MS,SIMULATION_MODE?"ON":"OFF");
  if(PIN_STATUS_LED>=0)pinMode(PIN_STATUS_LED,OUTPUT);if(PIN_BUZZER>=0)pinMode(PIN_BUZZER,OUTPUT);
  sensors.begin(); network.begin();
}
void loop(){
  const uint32_t now=millis(); sensors.update(now);const SensorReadings& r=sensors.readings();
  HazardAssessment h=hazards.update(r,now);
  if(h.newAlert){Serial.printf("[ALERT] type=%s severity=%s sensor=%s observed=%.2f %s threshold=%.2f %s reason=%s\n",h.eventType,severityName(h.severity),h.sourceSensor,h.observedValue,h.unit,h.thresholdValue,h.unit,h.reason);if(!network.enqueue(r,h))Serial.println("[ERROR] qualified alert remains local because outbound queue is unavailable/full");}
  if(now-lastTelemetry>=TELEMETRY_INTERVAL_MS){lastTelemetry=now;HazardAssessment telemetry=h;telemetry.newAlert=false;telemetry.eventType="TELEMETRY";network.enqueue(r,telemetry);}
  if(now-lastSummary>=5000){lastSummary=now;Serial.printf("[STATUS] hazard=%s mpu=%s dht=%s mq2=%s warm=%s calibrated=%s temp=%.1fC humidity=%.1f%% accel=%.2fG dynamic=%.2fG mq2=%uADC baseline=%uADC wifi=%s uptime=%lus\n",severityName(h.severity),r.mpuAvailable?"OK":"FAULT",r.dhtValid?"OK":"FAULT",r.mq2Available?"OK":"FAULT",r.mq2Warmed?"yes":"no",r.mq2Calibrated?"yes":"no",r.temperatureC,r.humidityPercent,r.accelerationMagnitudeG,r.dynamicAccelerationG,r.mq2FilteredAdc,r.mq2BaselineAdc,WiFi.status()==WL_CONNECTED?"connected":"offline",(unsigned long)(now/1000));}
  if(PIN_STATUS_LED>=0)digitalWrite(PIN_STATUS_LED,h.severity==HazardSeverity::CRITICAL?HIGH:LOW);
  delay(SENSOR_TICK_MS);
}
