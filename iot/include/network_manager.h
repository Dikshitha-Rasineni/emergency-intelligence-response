#pragma once
#include "data_models.h"
// Outbound delivery. Alerts go to a persistent NVS queue (survive reboot) and are removed only
// after a backend acknowledgement. Routine telemetry uses a small RAM queue and may be dropped.
// Transport: Wi-Fi first; SIM800L GPRS fallback for alerts when enabled.
class NetworkManager {
 public:
  void begin();
  bool enqueue(const SensorReadings& r, const HazardAssessment& h);
  uint32_t pendingAlerts();
 private:
  static void taskEntry(void*);
  void run();
};
