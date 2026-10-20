#pragma once
#include "data_models.h"
class SensorManager {
 public:
  void begin();
  void update(uint32_t now);
  const SensorReadings& readings() const { return r; }
  bool hardwareReady() const { return r.mpuAvailable || r.dhtAvailable || r.mq2Available; }
 private:
  SensorReadings r;
  void sampleMpu(uint32_t now); void sampleMq2(uint32_t now); void sampleDht(uint32_t now);
  uint32_t lastMpu=0, lastMq2=0, lastDht=0, bootMs=0, baselineStart=0;
  uint32_t mq2Sum=0, mq2Count=0;
  float magFilter=0, vibrationSqSum=0; uint8_t vibrationN=0;
};
