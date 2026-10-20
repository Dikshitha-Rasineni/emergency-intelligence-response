#pragma once
#include "data_models.h"
class HazardDetector {
 public: HazardAssessment update(const SensorReadings& r,uint32_t now);
 private: uint32_t gasSince=0,tempSince=0,lastAlert=0; uint8_t motionHits=0; bool gasLatched=false,tempLatched=false,motionAlertSent=false,gasAlertSent=false,tempAlertSent=false;
};
