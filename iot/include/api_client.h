#pragma once
#include <Arduino.h>
#include "data_models.h"
// Builds the JSON body once (stored in the persistent queue) and sends it later.
// A delivery counts only when the backend returns 2xx with a reading_id (201 new, 200 duplicate).
class ApiClient {
 public:
  bool configured() const;
  String buildPayload(const SensorReadings& r, const HazardAssessment& h, const char* eventId, bool wifi, uint32_t uptime) const;
  bool sendWifi(const String& body);
  bool sendGprs(const String& body);
};
