#include "hazard_detector.h"
#include "config.h"
HazardAssessment HazardDetector::update(const SensorReadings& r,uint32_t now){
  HazardAssessment a;
  const bool ready=r.mq2Warmed&&r.mq2Calibrated&&r.mq2Available;
  const int delta=ready?(int)r.mq2FilteredAdc-(int)r.mq2BaselineAdc:0;
  if(ready&&delta>=MQ2_WARNING_DELTA_ADC){if(!gasSince)gasSince=now;if(now-gasSince>=MQ2_PERSIST_MS){a.gasWarning=true;if(!gasLatched){gasLatched=true;gasAlertSent=false;}}} else if(!ready||delta<(int)MQ2_WARNING_DELTA_ADC-(int)MQ2_HYSTERESIS_ADC){gasSince=0;gasLatched=false;gasAlertSent=false;}
  if(r.dhtValid&&r.temperatureC>=TEMP_WARNING_C){if(!tempSince)tempSince=now;if(now-tempSince>=TEMP_PERSIST_MS){a.temperatureWarning=true;if(!tempLatched){tempLatched=true;tempAlertSent=false;}}} else if(!r.dhtValid||r.temperatureC<TEMP_WARNING_C-TEMP_HYSTERESIS_C){tempSince=0;tempLatched=false;tempAlertSent=false;}
  a.gasCritical=ready&&delta>=MQ2_CRITICAL_DELTA_ADC&&gasLatched;
  a.temperatureCritical=r.dhtValid&&r.temperatureC>=TEMP_CRITICAL_C&&tempLatched;
  if(r.impactCandidate){if(motionHits<255)motionHits++;}else motionHits=0;
  a.abnormalMotion=motionHits>=IMPACT_CONFIRM_SAMPLES; if(!a.abnormalMotion)motionAlertSent=false;
  const bool critical=a.gasCritical||a.temperatureCritical||a.abnormalMotion;
  const bool warning=a.gasWarning||a.temperatureWarning;
  bool emitMotion=false,emitGas=false,emitTemperature=false;
  if(critical)a.severity=HazardSeverity::CRITICAL;
  else if(warning)a.severity=HazardSeverity::WARNING;
  else if(!r.mpuAvailable||!r.dhtValid||!ready)a.severity=HazardSeverity::SENSOR_FAULT;
  if(a.abnormalMotion&&!motionAlertSent){a.eventType="ACCIDENT";a.sourceSensor="mpu6050";a.unit="g";a.observedValue=r.accelerationMagnitudeG;a.thresholdValue=IMPACT_THRESHOLD_G;a.reason="qualified_abnormal_motion";if(r.accelerationMagnitudeG<IMPACT_THRESHOLD_G){a.observedValue=r.dynamicAccelerationG;a.thresholdValue=VIBRATION_THRESHOLD_G;a.reason="persistent_abnormal_vibration";}a.newAlert=true;emitMotion=true;}
  else if(a.gasCritical&&!gasAlertSent){a.eventType="FIRE";a.sourceSensor="mq2_analog";a.unit="adc_delta";a.observedValue=delta;a.thresholdValue=MQ2_CRITICAL_DELTA_ADC;a.reason="mq2_analog_threshold";a.newAlert=true;emitGas=true;}
  else if(a.temperatureCritical&&!tempAlertSent){a.eventType="FIRE";a.sourceSensor="dht22";a.unit="celsius";a.observedValue=r.temperatureC;a.thresholdValue=TEMP_CRITICAL_C;a.reason="high_temperature";a.newAlert=true;emitTemperature=true;}
  if(a.newAlert&&lastAlert&&now-lastAlert<ALERT_REPEAT_COOLDOWN_MS)a.newAlert=false;
  if(a.newAlert){lastAlert=now;if(emitMotion)motionAlertSent=true;if(emitGas)gasAlertSent=true;if(emitTemperature)tempAlertSent=true;}
  return a;
}
