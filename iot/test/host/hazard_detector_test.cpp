#include <cassert>
#include <cstdio>
#include <string>
#include "config.h"
#include "hazard_detector.h"

static SensorReadings baseline(){SensorReadings r;r.mpuAvailable=r.dhtAvailable=r.mq2Available=true;r.dhtValid=true;r.mq2Warmed=r.mq2Calibrated=true;r.temperatureC=24;r.mq2BaselineAdc=500;r.mq2FilteredAdc=500;return r;}
int main(){
  auto r=baseline();HazardDetector d;
  auto a=d.update(r,100);assert(a.severity==HazardSeverity::NORMAL&&!a.newAlert);

  // Below warning: no alert. Persistent warning does not automatically become an incident.
  r.mq2FilteredAdc=500+MQ2_WARNING_DELTA_ADC-1;
  a=d.update(r,200);assert(!a.gasWarning&&!a.newAlert);

  // At the warning threshold, persistence raises WARNING but does not emit an incident.
  r.mq2FilteredAdc=500+MQ2_WARNING_DELTA_ADC;
  a=d.update(r,1000);assert(!a.gasWarning&&!a.newAlert);
  a=d.update(r,1000+MQ2_PERSIST_MS+1);assert(a.gasWarning&&!a.gasCritical&&!a.newAlert);
  // Escalation to critical emits one FIRE event.
  r.mq2FilteredAdc=500+MQ2_CRITICAL_DELTA_ADC;
  a=d.update(r,7000);assert(a.gasCritical&&a.newAlert&&a.eventType[0]=='F');
  a=d.update(r,57000);assert(!a.newAlert);

  // Hysteresis recovery rearms the next distinct episode.
  r.mq2FilteredAdc=500+MQ2_WARNING_DELTA_ADC-MQ2_HYSTERESIS_ADC-1;
  a=d.update(r,70000);assert(!a.gasWarning);
  r.mq2FilteredAdc=500+MQ2_CRITICAL_DELTA_ADC;
  a=d.update(r,80000);a=d.update(r,80000+MQ2_PERSIST_MS+1);assert(a.newAlert);

  // Invalid DHT readings are not treated as 0 C and therefore cannot be hot alerts.
  r=baseline();r.dhtValid=false;r.temperatureC=NAN;HazardDetector dht;
  a=dht.update(r,100);assert(!a.temperatureWarning&&!a.temperatureCritical);
  r=baseline();r.temperatureC=TEMP_CRITICAL_C;HazardDetector hot;
  a=hot.update(r,100);assert(!a.temperatureCritical);
  a=hot.update(r,100+TEMP_PERSIST_MS+1);assert(a.temperatureCritical&&a.newAlert&&a.eventType[0]=='F');

  // Motion needs confirmation and a single episode emits only one alert.
  r=baseline();r.impactCandidate=true;HazardDetector motion;
  a=motion.update(r,100);assert(!a.newAlert);a=motion.update(r,200);assert(!a.newAlert);
  a=motion.update(r,300);assert(a.newAlert&&a.eventType[0]=='A');
  a=motion.update(r,400);assert(!a.newAlert);
  r.impactCandidate=false;motion.update(r,500);r.impactCandidate=true;
  motion.update(r,61000);motion.update(r,61100);a=motion.update(r,61200);assert(a.newAlert);

  r=baseline();r.mpuAvailable=r.dhtValid=r.mq2Available=false;r.mq2Warmed=r.mq2Calibrated=false;
  HazardDetector fault;a=fault.update(r,100);assert(a.severity==HazardSeverity::SENSOR_FAULT);
  r=baseline();r.dhtValid=false;HazardDetector partialFault;a=partialFault.update(r,100);assert(a.severity==HazardSeverity::SENSOR_FAULT);
  // Water level: needs persistence; critical emits one FLOOD event; recovers with hysteresis.
  r=baseline();r.waterAvailable=true;r.waterRawAdc=WATER_CRITICAL_ADC;HazardDetector water;
  a=water.update(r,100);assert(!a.newAlert&&!a.waterWarning);
  a=water.update(r,100+WATER_PERSIST_MS+1);assert(a.waterCritical&&a.newAlert&&std::string(a.eventType)=="FLOOD");
  a=water.update(r,200+WATER_PERSIST_MS);assert(!a.newAlert);
  r.waterRawAdc=WATER_WARNING_ADC-WATER_HYSTERESIS_ADC-1;a=water.update(r,30000);assert(!a.waterWarning);
  // Brief water splash below persistence never alerts.
  r=baseline();r.waterAvailable=true;r.waterRawAdc=WATER_CRITICAL_ADC;HazardDetector splash;
  splash.update(r,100);r.waterRawAdc=0;a=splash.update(r,2000);assert(!a.newAlert);

  // SOS pad: short taps are ignored, a held press emits one SOS, release re-arms.
  r=baseline();r.fsrAvailable=true;r.fsrRawAdc=FSR_PRESS_ADC+100;HazardDetector pad;
  a=pad.update(r,100);assert(!a.newAlert);
  a=pad.update(r,100+FSR_HOLD_MS/2);assert(!a.newAlert);
  a=pad.update(r,100+FSR_HOLD_MS);assert(a.newAlert&&std::string(a.eventType)=="SOS");
  a=pad.update(r,200+FSR_HOLD_MS);assert(!a.newAlert);
  r.fsrRawAdc=0;pad.update(r,5000);r.fsrRawAdc=FSR_PRESS_ADC+100;pad.update(r,5100);
  a=pad.update(r,5100+FSR_HOLD_MS);assert(a.newAlert);  // not blocked by the 60 s cooldown

  char id[64];formatEventId(id,sizeof id,"RESQ-ESP32-001",7,42);assert(std::string(id)=="RESQ-ESP32-001:7:42");
  std::puts("hazard_detector_test: all cases passed");
}
