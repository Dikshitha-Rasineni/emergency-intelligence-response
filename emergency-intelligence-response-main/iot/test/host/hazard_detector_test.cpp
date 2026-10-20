#include <cassert>
#include <cstdio>
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
  std::puts("hazard_detector_test: all cases passed");
}
