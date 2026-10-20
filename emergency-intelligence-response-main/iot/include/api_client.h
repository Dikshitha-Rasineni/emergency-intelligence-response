#pragma once
#include <Arduino.h>
#include "data_models.h"
class ApiClient { public: bool post(const SensorReadings& r,const HazardAssessment& h,bool wifi,uint32_t uptime); bool configured() const; };
