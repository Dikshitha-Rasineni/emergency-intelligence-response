#include "gsm_link.h"
#include "config.h"
#if __has_include("secrets.h")
#include "secrets.h"
#endif
#ifndef RESQ_GPRS_APN
#define RESQ_GPRS_APN ""
#define RESQ_GPRS_USER ""
#define RESQ_GPRS_PASS ""
#define RESQ_GPRS_HOST ""
#define RESQ_GPRS_PORT 80
#endif
#ifndef RESQ_DEVICE_TOKEN
#define RESQ_DEVICE_TOKEN ""
#endif
#define TINY_GSM_MODEM_SIM800
#define TINY_GSM_RX_BUFFER 1024
#include <TinyGsmClient.h>
#include <ArduinoHttpClient.h>

static HardwareSerial simSerial(2);
static TinyGsm modem(simSerial);
static TinyGsmClient client(modem);
static bool started = false;
static uint32_t lastAttempt = 0;

void GsmLink::begin() {
  if (!ENABLE_SIM800L) return;
  simSerial.begin(SIM_BAUD, SERIAL_8N1, PIN_SIM_RX, PIN_SIM_TX);
  started = modem.restart();
  Serial.printf("[GPRS] SIM800L %s\n", started ? modem.getModemInfo().c_str() : "not responding (check 4 V / 2 A supply and wiring)");
  if (!GPRS_ALLOW_PLAINTEXT) Serial.println("[GPRS] disabled: GPRS_ALLOW_PLAINTEXT=false (SIM800L lacks modern TLS)");
}

bool GsmLink::ready() {
  if (!ENABLE_SIM800L || !GPRS_ALLOW_PLAINTEXT || !started || strlen(RESQ_GPRS_HOST) == 0) return false;
  if (modem.isGprsConnected()) return true;
  if (lastAttempt && millis() - lastAttempt < GPRS_RETRY_MS) return false;
  lastAttempt = millis();
  if (!modem.waitForNetwork(30000)) { Serial.println("[GPRS] no cellular network"); return false; }
  if (!modem.gprsConnect(RESQ_GPRS_APN, RESQ_GPRS_USER, RESQ_GPRS_PASS)) { Serial.println("[GPRS] attach failed"); return false; }
  Serial.println("[GPRS] attached");
  return true;
}

bool GsmLink::post(const String& body, int& httpCode, String& response) {
  if (!ready()) return false;
  HttpClient http(client, RESQ_GPRS_HOST, RESQ_GPRS_PORT);
  http.setTimeout(15000);
  http.beginRequest();
  http.post("/api/v1/iot/events");
  http.sendHeader("Content-Type", "application/json");
  http.sendHeader("Content-Length", body.length());
  if (strlen(RESQ_DEVICE_TOKEN)) http.sendHeader("Authorization", String("Bearer ") + RESQ_DEVICE_TOKEN);
  http.beginBody();
  http.print(body);
  http.endRequest();
  httpCode = http.responseStatusCode();
  response = http.responseBody();
  http.stop();
  return httpCode > 0;
}
