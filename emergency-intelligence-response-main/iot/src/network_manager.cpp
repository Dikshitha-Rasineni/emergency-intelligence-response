#include "network_manager.h"
#include "api_client.h"
#include "config.h"
#include <WiFi.h>
#if __has_include("secrets.h")
#include "secrets.h"
#else
#define RESQ_WIFI_SSID ""
#define RESQ_WIFI_PASSWORD ""
#endif
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include <freertos/task.h>

struct Job { SensorReadings readings; HazardAssessment hazard; uint8_t attempts; };
static QueueHandle_t regularQ=nullptr, urgentQ=nullptr;
static uint32_t retryMs=WIFI_RETRY_BASE_MS, nextAttempt=0;
static bool attempted=false, taskStarted=false; static ApiClient client;
static bool wasConnected=false;
void NetworkManager::begin(){
  regularQ=xQueueCreate(OFFLINE_QUEUE_CAPACITY-2,sizeof(Job));urgentQ=xQueueCreate(2,sizeof(Job));
  if(!regularQ||!urgentQ){Serial.println("[ERROR] outbound queue allocation failed; sensor sampling remains active");return;}
  WiFi.mode(WIFI_STA);WiFi.setAutoReconnect(false);
  if(!strlen(RESQ_WIFI_SSID))Serial.println("[WARN] Wi-Fi credentials missing; sampling continues offline");
  Serial.printf("[INIT] backend URL %s; server-side device auth is not supported by the current backend\n",client.configured()?"configured":"missing");
  if(!client.configured())Serial.println("[WARN] backend URL missing; telemetry remains local");
  if(!SIMULATION_MODE&&!hasConfiguredLocation())Serial.println("[WARN] backend requires real installation coordinates; telemetry and alerts remain local");
  taskStarted=xTaskCreatePinnedToCore(taskEntry,"resq-network",8192,nullptr,1,nullptr,0)==pdPASS;
  if(!taskStarted)Serial.println("[ERROR] network task allocation failed; sensor sampling remains active");
}
bool NetworkManager::enqueue(const SensorReadings& r,const HazardAssessment& h){
  if(!taskStarted||!regularQ||!urgentQ)return false;
  if(SIMULATION_MODE&&!ALLOW_SIMULATION_UPLOAD)return true;
  if(!client.configured())return true;
  if(!SIMULATION_MODE&&!hasConfiguredLocation())return true;
  Job j{r,h,0}; QueueHandle_t q=h.newAlert?urgentQ:regularQ;
  if(xQueueSend(q,&j,0)==pdTRUE)return true;
  if(h.newAlert){Job discarded;if(xQueueReceive(regularQ,&discarded,0)==pdTRUE){Serial.println("[WARN] evicted routine telemetry to preserve urgent alert");if(xQueueSend(urgentQ,&j,0)==pdTRUE)return true;}}
  if(h.newAlert&&xQueueSend(regularQ,&j,0)==pdTRUE){Serial.println("[WARN] urgent queue full; alert placed in regular queue");return true;}
  Serial.printf("[WARN] outbound queue full; %s dropped\n",h.newAlert?"alert":"telemetry");return false;
}
void NetworkManager::taskEntry(void* p){static NetworkManager n;n.run();}
void NetworkManager::run(){
  Job job; uint32_t lastPost=0;
  for(;;){const uint32_t now=millis();
    if(strlen(RESQ_WIFI_SSID)&&WiFi.status()!=WL_CONNECTED&&(!attempted||(int32_t)(now-nextAttempt)>=0)){
      attempted=true;WiFi.begin(RESQ_WIFI_SSID,RESQ_WIFI_PASSWORD);nextAttempt=now+retryMs;retryMs=min<uint32_t>(retryMs*2,WIFI_RETRY_MAX_MS);Serial.println("[WIFI] connection attempt started");
    }
    const bool connected=WiFi.status()==WL_CONNECTED;
    if(connected&&!wasConnected)Serial.printf("[WIFI] connected IP=%s\n",WiFi.localIP().toString().c_str());
    if(!connected&&wasConnected)Serial.println("[WARN] Wi-Fi disconnected; telemetry queue retained");
    wasConnected=connected;
    if(connected){retryMs=WIFI_RETRY_BASE_MS;
      if(now-lastPost>=API_MIN_INTERVAL_MS){bool have=xQueueReceive(urgentQ,&job,0)==pdTRUE;if(!have)have=xQueueReceive(regularQ,&job,0)==pdTRUE;
        if(have){lastPost=now;if(!client.post(job.readings,job.hazard,true,now)){// bounded retries per online request attempt
          if(++job.attempts<3){if(xQueueSend(job.hazard.newAlert?urgentQ:regularQ,&job,0)!=pdTRUE)Serial.println("[WARN] failed API job dropped; queue full");}
          else Serial.printf("[ERROR] dropping job after bounded retries (%s)\n",job.hazard.newAlert?"alert":"telemetry");
          vTaskDelay(pdMS_TO_TICKS(1000));
        }}
      }
    }
    vTaskDelay(pdMS_TO_TICKS(100));
  }
}
