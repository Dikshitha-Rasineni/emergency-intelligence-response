#include "sensor_manager.h"
#include "config.h"
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <math.h>

static Adafruit_MPU6050 mpu;
static DHT dht(PIN_DHT22, DHT22);
void SensorManager::begin() {
  bootMs=millis(); baselineStart=0;
  Wire.begin(PIN_I2C_SDA,PIN_I2C_SCL);
  r.mpuAvailable=mpu.begin(MPU6050_ADDRESS,&Wire);
  if(r.mpuAvailable){ mpu.setAccelerometerRange(MPU6050_RANGE_16_G); mpu.setFilterBandwidth(MPU6050_BAND_21_HZ); }
  dht.begin(); r.dhtAvailable=true;
  analogReadResolution(12);
  pinMode(PIN_MQ2_ADC,INPUT); analogSetPinAttenuation(PIN_MQ2_ADC,ADC_11db); r.mq2Available=true;
  pinMode(PIN_WATER_ADC,INPUT); analogSetPinAttenuation(PIN_WATER_ADC,ADC_11db); r.waterAvailable=true;
  pinMode(PIN_FSR_ADC,INPUT); analogSetPinAttenuation(PIN_FSR_ADC,ADC_11db); r.fsrAvailable=true;
  Serial.printf("[INIT] MPU6050=%s DHT22=started MQ2=GPIO%d WATER=GPIO%d FSR=GPIO%d\n",r.mpuAvailable?"OK":"UNAVAILABLE",PIN_MQ2_ADC,PIN_WATER_ADC,PIN_FSR_ADC);
}
void SensorManager::update(uint32_t now){
  if(SIMULATION_MODE){
    r.simulated=true;r.mpuAvailable=r.dhtAvailable=r.mq2Available=true;r.dhtValid=true;r.mq2Warmed=r.mq2Calibrated=true;
    r.temperatureC=25.0f;r.humidityPercent=45.0f;r.mq2BaselineAdc=500;r.waterAvailable=r.fsrAvailable=true;r.waterRawAdc=100;r.fsrRawAdc=0;
    r.mq2FilteredAdc=500+((now/20000)%3==1?MQ2_WARNING_DELTA_ADC+30:0);r.mq2RawAdc=r.mq2FilteredAdc;
    r.accelerationMagnitudeG=1.0f;r.accelerationMagnitudeMps2=9.80665f;r.dynamicAccelerationG=0.0f;r.gxDps=r.gyDps=r.gzDps=0.0f;r.impactCandidate=((now/45000)%4==2)&&(now%3000<300);r.vibrationRmsG=0.02f;
    r.lastMpuMs=r.lastMq2Ms=r.lastDhtMs=now;return;
  }
  if(now-lastMpu>=MPU_SAMPLE_MS){lastMpu=now;sampleMpu(now);}
  if(now-lastMq2>=MQ2_SAMPLE_MS){lastMq2=now;sampleMq2(now);}
  if(now-lastDht>=DHT_SAMPLE_MS){lastDht=now;sampleDht(now);}
  if(now-lastWater>=WATER_SAMPLE_MS){lastWater=now;sampleWater(now);}
  if(now-lastFsr>=FSR_SAMPLE_MS){lastFsr=now;sampleFsr(now);}
}
// Floating/disconnected analog inputs are not detectable from one sample; treat the
// value as raw ADC counts (not depth or force) and calibrate thresholds on the real module.
void SensorManager::sampleWater(uint32_t now){
  static uint16_t ring[5]={}; static uint8_t n=0,at=0; ring[at++%5]=analogRead(PIN_WATER_ADC); if(n<5)n++;
  uint32_t sum=0; for(uint8_t i=0;i<n;i++)sum+=ring[i]; r.waterRawAdc=sum/n; r.lastWaterMs=now;
}
void SensorManager::sampleFsr(uint32_t now){ r.fsrRawAdc=analogRead(PIN_FSR_ADC); r.lastFsrMs=now; }
void SensorManager::sampleMpu(uint32_t now){
  Wire.beginTransmission(MPU6050_ADDRESS);
  if(Wire.endTransmission()!=0){if(r.mpuAvailable)Serial.println("[ERROR] MPU6050 disconnected");r.mpuAvailable=false;return;}
  if(!r.mpuAvailable){r.mpuAvailable=mpu.begin(MPU6050_ADDRESS,&Wire);if(r.mpuAvailable){mpu.setAccelerometerRange(MPU6050_RANGE_16_G);mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);Serial.println("[INFO] MPU6050 recovered");}return;}
  sensors_event_t a,g,t; mpu.getEvent(&a,&g,&t);
  if(!isfinite(a.acceleration.x)||!isfinite(a.acceleration.y)||!isfinite(a.acceleration.z)) {r.mpuAvailable=false;Serial.println("[ERROR] MPU6050 invalid reading; marked unavailable");return;}
  r.ax=a.acceleration.x;r.ay=a.acceleration.y;r.az=a.acceleration.z;
  constexpr float RAD_TO_DEG_F=57.2957795f;r.gxDps=g.gyro.x*RAD_TO_DEG_F;r.gyDps=g.gyro.y*RAD_TO_DEG_F;r.gzDps=g.gyro.z*RAD_TO_DEG_F;
  const float mag=sqrtf(r.ax*r.ax+r.ay*r.ay+r.az*r.az);
  if(!isfinite(mag)||mag>200.0f){r.mpuAvailable=false;return;}
  magFilter=magFilter==0?mag:0.25f*mag+0.75f*magFilter;
  r.accelerationMagnitudeMps2=magFilter;r.accelerationMagnitudeG=magFilter/9.80665f;
  r.dynamicAccelerationG=fabsf(magFilter-9.80665f)/9.80665f;
  const float dynamic=fabsf(mag-9.80665f)/9.80665f; vibrationSqSum+=dynamic*dynamic; if(++vibrationN>=10){r.vibrationRmsG=sqrtf(vibrationSqSum/vibrationN);vibrationSqSum=0;vibrationN=0;}
  r.impactCandidate=r.accelerationMagnitudeG>=IMPACT_THRESHOLD_G || r.dynamicAccelerationG>=VIBRATION_THRESHOLD_G; r.lastMpuMs=now;
}
void SensorManager::sampleMq2(uint32_t now){
  const int value=analogRead(PIN_MQ2_ADC); if(value<0||value>4095){r.mq2Available=false;return;}
  r.mq2RawAdc=value; static uint16_t ring[8]={}; static uint8_t n=0, at=0; ring[at++%8]=value; if(n<8)n++;
  uint32_t sum=0; for(uint8_t i=0;i<n;i++)sum+=ring[i]; r.mq2FilteredAdc=sum/n; r.lastMq2Ms=now;
  r.mq2Warmed=(uint32_t)(now-bootMs)>=MQ2_WARMUP_MS;
  if(r.mq2Warmed&&!r.mq2Calibrated){if(!baselineStart){baselineStart=now;mq2Sum=0;mq2Count=0;Serial.println("[INFO] MQ2 warm-up complete; clean-air baseline calibration started");}
    mq2Sum+=r.mq2FilteredAdc;mq2Count++; if(mq2Count>=MQ2_BASELINE_SAMPLES && now-baselineStart>=MQ2_BASELINE_WINDOW_MS){r.mq2BaselineAdc=mq2Sum/mq2Count;r.mq2Calibrated=true;Serial.printf("[INFO] MQ2 baseline=%u ADC (not ppm)\n",r.mq2BaselineAdc);}}
}
void SensorManager::sampleDht(uint32_t now){
  const float t=dht.readTemperature(), h=dht.readHumidity();
  r.dhtValid=isfinite(t)&&isfinite(h)&&t>=-40&&t<=80&&h>=0&&h<=100;
  r.dhtAvailable=true; r.temperatureC=r.dhtValid?t:NAN;r.humidityPercent=r.dhtValid?h:NAN;r.lastDhtMs=now;
  if(!r.dhtValid)Serial.println("[WARN] DHT22 returned invalid data; omitted from telemetry");
}
