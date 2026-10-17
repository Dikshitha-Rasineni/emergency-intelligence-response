#include <Arduino.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <WiFi.h>
#include <Wire.h>
#include <HardwareSerial.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include "config.h"

#if __has_include("secrets.h")
#include "secrets.h"
#else
#define RESQ_WIFI_SSID ""
#define RESQ_WIFI_PASSWORD ""
#endif

Adafruit_MPU6050 mpu;
DHT dht(DHT_PIN, DHT22);
Preferences prefs;
HardwareSerial sim800l(2);

struct Readings { float impactG=NAN, temperatureC=NAN, smokePpm=NAN, waterCm=NAN; int fsrRaw=0, soundRaw=0; bool mpuOk=false, dhtOk=false, locationOk=false, sim800Ok=false; };
struct PendingEvent { String json; bool emergency; };
PendingEvent queueItems[EVENT_QUEUE_CAPACITY];
Readings readings;
uint8_t mpuAddress=0;
uint8_t queueCount=0, impactHits=0;
uint32_t lastImpactMs=0,lastDhtMs=0,lastAnalogMs=0,lastTelemetryMs=0,lastWifiAttemptMs=0,lastDrainMs=0,lastEmergencyMs=0,lastSim800Ms=0,lastMpuLogMs=0;
bool fireLatched=false, floodLatched=false;

bool validCoordinates() { return FIXED_LATITUDE>=-90 && FIXED_LATITUDE<=90 && FIXED_LONGITUDE>=-180 && FIXED_LONGITUDE<=180 && !(FIXED_LATITUDE==0 && FIXED_LONGITUDE==0); }
void logStatus(const char* label,bool ok) { Serial.printf("[INIT] %-12s %s\n",label,ok?"OK":"UNAVAILABLE"); }

void persistQueue() {
  prefs.clear(); prefs.putUChar("count",queueCount);
  for(uint8_t i=0;i<queueCount;i++){ char key[8]; snprintf(key,sizeof(key),"e%u",i); prefs.putString(key,queueItems[i].json); }
}
void loadQueue() {
  queueCount=min<uint8_t>(prefs.getUChar("count",0),EVENT_QUEUE_CAPACITY);
  for(uint8_t i=0;i<queueCount;i++){ char key[8]; snprintf(key,sizeof(key),"e%u",i); queueItems[i]={prefs.getString(key,""),true}; }
  Serial.printf("[QUEUE] restored=%u/%u\n",queueCount,EVENT_QUEUE_CAPACITY);
}
bool enqueue(const String& json,bool emergency) {
  if(queueCount>=EVENT_QUEUE_CAPACITY){ if(!emergency){Serial.println("[QUEUE] full; telemetry dropped");return false;} uint8_t victim=0; while(victim<queueCount&&queueItems[victim].emergency) victim++; if(victim==queueCount){Serial.println("[QUEUE] full of emergencies; event not persisted");return false;} for(uint8_t i=victim;i+1<queueCount;i++) queueItems[i]=queueItems[i+1]; --queueCount; }
  queueItems[queueCount++]={json,emergency}; persistQueue(); return true;
}
void removeHead(){ for(uint8_t i=1;i<queueCount;i++) queueItems[i-1]=queueItems[i]; if(queueCount)--queueCount; persistQueue(); }

bool postJson(const String& json) {
  if(WiFi.status()!=WL_CONNECTED)return false; WiFiClient client; HTTPClient http; String url=String(API_BASE_URL)+API_PATH;
  if(!http.begin(client,url))return false; http.setTimeout(HTTP_TIMEOUT_MS); http.addHeader("Content-Type","application/json"); int code=http.POST(json); bool ok=code>=200&&code<300;
  if(ok){ DynamicJsonDocument response(1024); auto err=deserializeJson(response,http.getString()); if(err||response["reading_id"].isNull())ok=false; else Serial.printf("[API] acknowledged reading=%s incident=%s\n",response["reading_id"]|"?",response["incident_id"]|"none"); }
  else Serial.printf("[API] HTTP failure=%d\n",code); http.end(); return ok;
}
void drainQueue(){ if(!queueCount||WiFi.status()!=WL_CONNECTED||millis()-lastDrainMs<QUEUE_DRAIN_INTERVAL_MS)return; lastDrainMs=millis(); if(postJson(queueItems[0].json))removeHead(); }

String makeEvent(const char* type){
  DynamicJsonDocument doc(768); doc["device_id"]=DEVICE_ID; doc["event_type"]=type;
  if(isfinite(readings.temperatureC))doc["temperature"]=readings.temperatureC; if(isfinite(readings.smokePpm))doc["smoke_level"]=readings.smokePpm; if(isfinite(readings.waterCm))doc["water_level"]=readings.waterCm; if(isfinite(readings.impactG))doc["impact"]=readings.impactG;
  doc["latitude"]=FIXED_LATITUDE; doc["longitude"]=FIXED_LONGITUDE; String result; serializeJson(doc,result); return result;
}
void submit(const char* type,bool emergency){ if(!readings.locationOk){Serial.println("[EVENT] withheld: no valid coordinates");return;} String json=makeEvent(type); if(!postJson(json))enqueue(json,emergency); else Serial.printf("[EVENT] delivered type=%s\n",type); }

void scanI2cBus(){
  uint8_t found=0;
  Serial.println("[I2C] scanning...");
  for(uint8_t address=1;address<127;address++){
    Wire.beginTransmission(address);
    uint8_t error=Wire.endTransmission();
    if(error==0){Serial.printf("[I2C] device=0x%02X\n",address);found++;}
    yield();
  }
  if(!found)Serial.println("[I2C] no devices found");
}
bool readI2cRegister(uint8_t address,uint8_t reg,uint8_t &value){
  Wire.beginTransmission(address);
  Wire.write(reg);
  if(Wire.endTransmission(false)!=0)return false;
  if(Wire.requestFrom((int)address,1)!=1)return false;
  value=Wire.read();
  return true;
}
void sampleImpact(){
  if(!readings.mpuOk)return; sensors_event_t a,g,temp; mpu.getEvent(&a,&g,&temp); float magnitudeG=sqrtf(a.acceleration.x*a.acceleration.x+a.acceleration.y*a.acceleration.y+a.acceleration.z*a.acceleration.z)/9.80665f; readings.impactG=magnitudeG; if(millis()-lastMpuLogMs>=1000){lastMpuLogMs=millis();Serial.printf("[MPU6050] ax=%.2f ay=%.2f az=%.2f m/s2 total=%.3fG\\n",a.acceleration.x,a.acceleration.y,a.acceleration.z,magnitudeG);}
  if(magnitudeG>=IMPACT_THRESHOLD_G)++impactHits;else impactHits=0;
  if(impactHits>=IMPACT_QUALIFYING_SAMPLES&&millis()-lastEmergencyMs>=EMERGENCY_COOLDOWN_MS){lastEmergencyMs=millis();impactHits=0;submit("ACCIDENT",true);}
}
void sampleSensors(){
  uint32_t now=millis(); if(now-lastImpactMs>=IMPACT_SAMPLE_MS){lastImpactMs=now;sampleImpact();}
  if(HAS_DHT&&now-lastDhtMs>=DHT_SAMPLE_MS){lastDhtMs=now;float t=dht.readTemperature();readings.dhtOk=isfinite(t)&&t>=-40&&t<=150;readings.temperatureC=readings.dhtOk?t:NAN;}
  if(now-lastAnalogMs>=ANALOG_SAMPLE_MS){lastAnalogMs=now; if(HAS_FSR)readings.fsrRaw=analogRead(FSR_PIN); if(HAS_SOUND)readings.soundRaw=analogRead(SOUND_PIN); if(HAS_MQ2&&now>=MQ2_WARMUP_MS)readings.smokePpm=max(0.0f,(analogRead(MQ2_PIN)-MQ2_BASELINE_ADC)*MQ2_SLOPE_PPM_PER_ADC); if(HAS_WATER_SENSOR)readings.waterCm=max(0.0f,(analogRead(WATER_PIN)-WATER_ADC_OFFSET)*WATER_CM_PER_ADC);
    bool fire=(isfinite(readings.smokePpm)&&readings.smokePpm>=FIRE_SMOKE_THRESHOLD_PPM)||(isfinite(readings.temperatureC)&&readings.temperatureC>=FIRE_TEMPERATURE_C); bool flood=isfinite(readings.waterCm)&&readings.waterCm>=FLOOD_WATER_CM;
    if(fire&&!fireLatched&&now-lastEmergencyMs>=EMERGENCY_COOLDOWN_MS){fireLatched=true;lastEmergencyMs=now;submit("FIRE",true);} if(!fire)fireLatched=false;
    if(flood&&!floodLatched&&now-lastEmergencyMs>=EMERGENCY_COOLDOWN_MS){floodLatched=true;lastEmergencyMs=now;submit("FLOOD",true);} if(!flood)floodLatched=false;
  }
}
void pollSim800L(){
  if(!HAS_SIM800L || millis()-lastSim800Ms<SIM800L_POLL_MS)return;
  lastSim800Ms=millis();
  while(sim800l.available())(void)sim800l.read();
  sim800l.print("AT\r\n");
  uint32_t deadline=millis()+SIM800L_TIMEOUT_MS;
  String response;
  while((int32_t)(deadline-millis())>0){
    while(sim800l.available() && response.length()<160)response+=(char)sim800l.read();
    yield();
  }
  readings.sim800Ok=response.indexOf("OK")>=0;
  Serial.printf("[SIM800L] AT %s; response=%s\n",readings.sim800Ok?"OK":"FAILED",response.length()?"received":"none");
}
void maintainWiFi(){ if(!strlen(RESQ_WIFI_SSID))return; if(WiFi.status()==WL_CONNECTED)return; if(millis()-lastWifiAttemptMs<WIFI_RETRY_MS)return; lastWifiAttemptMs=millis(); WiFi.disconnect(); WiFi.begin(RESQ_WIFI_SSID,RESQ_WIFI_PASSWORD); Serial.println("[WIFI] connection attempt started"); }

void setup(){
  Serial.begin(115200); delay(200); Serial.printf("RESQ.AI firmware=%s device=%s\n",FIRMWARE_VERSION,DEVICE_ID); if(HAS_STATUS_LED)pinMode(STATUS_LED_PIN,OUTPUT); if(HAS_SOS)pinMode(SOS_PIN,INPUT_PULLUP); if(HAS_BUZZER)pinMode(BUZZER_PIN,OUTPUT); analogReadResolution(12);
  prefs.begin("resq-queue",false); loadQueue(); readings.locationOk=validCoordinates(); logStatus("location",readings.locationOk); Wire.begin(I2C_SDA_PIN,I2C_SCL_PIN); scanI2cBus(); uint8_t whoAmI=0; if(readI2cRegister(MPU6050_PRIMARY_ADDRESS,0x75,whoAmI))Serial.printf("[MPU6050] WHO_AM_I=0x%02X expected=0x68\\n",whoAmI); else Serial.println("[MPU6050] WHO_AM_I read failed"); readings.mpuOk=mpu.begin(MPU6050_PRIMARY_ADDRESS,&Wire); if(readings.mpuOk)mpuAddress=MPU6050_PRIMARY_ADDRESS; else if(mpu.begin(MPU6050_ALT_ADDRESS,&Wire)){readings.mpuOk=true;mpuAddress=MPU6050_ALT_ADDRESS;} logStatus("MPU6050",readings.mpuOk); if(readings.mpuOk){Serial.printf("[MPU6050] address=0x%02X\n",mpuAddress);mpu.setAccelerometerRange(MPU6050_RANGE_16_G);mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);} if(HAS_DHT){dht.begin();logStatus("DHT22",true);} logStatus("FSR",HAS_FSR); logStatus("sound",HAS_SOUND); logStatus("MQ-2",HAS_MQ2); logStatus("water",HAS_WATER_SENSOR); if(HAS_SIM800L){sim800l.begin(SIM800L_BAUD,SERIAL_8N1,SIM800L_RX_PIN,SIM800L_TX_PIN); lastSim800Ms=millis()-SIM800L_POLL_MS; Serial.printf("[INIT] SIM800L UART RX=%d TX=%d baud=%lu\n",SIM800L_RX_PIN,SIM800L_TX_PIN,(unsigned long)SIM800L_BAUD);} WiFi.mode(WIFI_STA);maintainWiFi();
  Serial.printf("[CFG] api=%s%s thresholds impact=%.1fG smoke=%.0fppm temp=%.1fC water=%.1fcm\n",API_BASE_URL,API_PATH,IMPACT_THRESHOLD_G,FIRE_SMOKE_THRESHOLD_PPM,FIRE_TEMPERATURE_C,FLOOD_WATER_CM);
}
void loop(){ sampleSensors();pollSim800L();maintainWiFi();drainQueue(); if(millis()-lastTelemetryMs>=TELEMETRY_INTERVAL_MS){lastTelemetryMs=millis();submit("TELEMETRY",false);} if(HAS_STATUS_LED)digitalWrite(STATUS_LED_PIN,WiFi.status()==WL_CONNECTED?HIGH:LOW);yield(); }

