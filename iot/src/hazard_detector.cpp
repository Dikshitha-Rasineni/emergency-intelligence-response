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
  // Water level: persistent rise above warning, critical with hysteresis.
  if(r.waterAvailable&&r.waterRawAdc>=WATER_WARNING_ADC){if(!waterSince)waterSince=now;if(now-waterSince>=WATER_PERSIST_MS){a.waterWarning=true;if(!waterLatched){waterLatched=true;waterAlertSent=false;}}}
  else if(!r.waterAvailable||r.waterRawAdc<WATER_WARNING_ADC-WATER_HYSTERESIS_ADC){waterSince=0;waterLatched=false;waterAlertSent=false;}
  a.waterCritical=r.waterAvailable&&r.waterRawAdc>=WATER_CRITICAL_ADC&&waterLatched;
  // SOS pad: a deliberate press held for FSR_HOLD_MS. Re-arms only after release.
  if(r.fsrAvailable&&r.fsrRawAdc>=FSR_PRESS_ADC){if(!fsrSince)fsrSince=now;a.sosPressed=now-fsrSince>=FSR_HOLD_MS;}
  else{fsrSince=0;sosAlertSent=false;}
  const bool critical=a.gasCritical||a.temperatureCritical||a.abnormalMotion||a.waterCritical||a.sosPressed;
  const bool warning=a.gasWarning||a.temperatureWarning||a.waterWarning;
  bool emitMotion=false,emitGas=false,emitTemperature=false,emitWater=false,emitSos=false;
  if(critical)a.severity=HazardSeverity::CRITICAL;
  else if(warning)a.severity=HazardSeverity::WARNING;
  else if(!r.mpuAvailable||!r.dhtValid||!ready)a.severity=HazardSeverity::SENSOR_FAULT;
  if(a.sosPressed&&!sosAlertSent){a.eventType="SOS";a.sourceSensor="fsr_pad";a.unit="adc";a.observedValue=r.fsrRawAdc;a.thresholdValue=FSR_PRESS_ADC;a.reason="sos_pad_held";a.newAlert=true;emitSos=true;}
  else if(a.abnormalMotion&&!motionAlertSent){a.eventType="ACCIDENT";a.sourceSensor="mpu6050";a.unit="g";a.observedValue=r.accelerationMagnitudeG;a.thresholdValue=IMPACT_THRESHOLD_G;a.reason="qualified_abnormal_motion";if(r.accelerationMagnitudeG<IMPACT_THRESHOLD_G){a.observedValue=r.dynamicAccelerationG;a.thresholdValue=VIBRATION_THRESHOLD_G;a.reason="persistent_abnormal_vibration";}a.newAlert=true;emitMotion=true;}
  else if(a.gasCritical&&!gasAlertSent){a.eventType="FIRE";a.sourceSensor="mq2_analog";a.unit="adc_delta";a.observedValue=delta;a.thresholdValue=MQ2_CRITICAL_DELTA_ADC;a.reason="mq2_analog_threshold";a.newAlert=true;emitGas=true;}
  else if(a.temperatureCritical&&!tempAlertSent){a.eventType="FIRE";a.sourceSensor="dht22";a.unit="celsius";a.observedValue=r.temperatureC;a.thresholdValue=TEMP_CRITICAL_C;a.reason="high_temperature";a.newAlert=true;emitTemperature=true;}
  else if(a.waterCritical&&!waterAlertSent){a.eventType="FLOOD";a.sourceSensor="water_level";a.unit="adc";a.observedValue=r.waterRawAdc;a.thresholdValue=WATER_CRITICAL_ADC;a.reason="water_level_threshold";a.newAlert=true;emitWater=true;}
  // A held SOS press is never suppressed by the cooldown of an unrelated earlier alert.
  if(a.newAlert&&!emitSos&&lastAlert&&now-lastAlert<ALERT_REPEAT_COOLDOWN_MS)a.newAlert=false;
  if(a.newAlert){lastAlert=now;if(emitMotion)motionAlertSent=true;if(emitGas)gasAlertSent=true;if(emitTemperature)tempAlertSent=true;if(emitWater)waterAlertSent=true;if(emitSos)sosAlertSent=true;}
  return a;
}
