#pragma once
#include <stdint.h>
#include <math.h>
#include <stdio.h>

enum class HazardSeverity : uint8_t { NORMAL, WARNING, CRITICAL, SENSOR_FAULT };
struct SensorReadings {
  bool mpuAvailable = false, dhtAvailable = false, mq2Available = false;
  bool dhtValid = false, mq2Warmed = false, mq2Calibrated = false;
  bool simulated = false;
  float ax = NAN, ay = NAN, az = NAN, accelerationMagnitudeMps2 = NAN;
  float gxDps = NAN, gyDps = NAN, gzDps = NAN;
  float accelerationMagnitudeG = NAN, dynamicAccelerationG = NAN, vibrationRmsG = NAN;
  float temperatureC = NAN, humidityPercent = NAN;
  uint16_t mq2RawAdc = 0, mq2FilteredAdc = 0, mq2BaselineAdc = 0;
  bool waterAvailable = false, fsrAvailable = false;
  uint16_t waterRawAdc = 0, fsrRawAdc = 0;
  uint32_t lastWaterMs = 0, lastFsrMs = 0;
  uint32_t lastMpuMs = 0, lastDhtMs = 0, lastMq2Ms = 0;
  bool impactCandidate = false;
};
struct HazardAssessment {
  HazardSeverity severity = HazardSeverity::NORMAL;
  bool gasWarning = false, gasCritical = false, temperatureWarning = false;
  bool temperatureCritical = false, abnormalMotion = false;
  bool waterWarning = false, waterCritical = false, sosPressed = false;
  bool newAlert = false;
  const char* eventType = "TELEMETRY";
  const char* reason = "normal";
  const char* sourceSensor = "";
  const char* unit = "";
  float observedValue = NAN, thresholdValue = NAN;
};
inline const char* severityName(HazardSeverity s) {
  switch (s) { case HazardSeverity::WARNING: return "warning"; case HazardSeverity::CRITICAL: return "critical";
    case HazardSeverity::SENSOR_FAULT: return "sensor_fault"; default: return "normal"; }
}

// Device-unique event id "<DEVICE_ID>:<boot>:<seq>" used by the backend for idempotency.
inline void formatEventId(char* out, unsigned len, const char* deviceId, uint32_t boot, uint32_t seq) {
  snprintf(out, len, "%s:%lu:%lu", deviceId, (unsigned long)boot, (unsigned long)seq);
}
