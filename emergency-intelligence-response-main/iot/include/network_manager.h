#pragma once
#include "data_models.h"
class NetworkManager {
 public: void begin(); bool enqueue(const SensorReadings& r,const HazardAssessment& h);
 private: static void taskEntry(void*); void run();
};
