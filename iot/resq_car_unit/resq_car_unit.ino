/*
  RESQ.AI in-car crash unit  (ESP32 + force/pressure sensor + SIM800L)
  -------------------------------------------------------------------
  Demo set-up: a force sensor (FSR) sits behind a fake dashboard in the car. Hitting it by hand
  simulates the crash force. The ESP32 reads the sensor, compares it with the threshold, and sends
  the reading to the RESQ.AI website over the SIM card. RESQ.AI creates the incident, GenAI writes
  every control room its brief, and the nearest units are dispatched.

  Flow:  read FSR fast -> force estimate (N) -> above THRESHOLD for >= CONFIRM_SAMPLES samples
         -> beep for CANCEL_WINDOW_S ("I'm OK" button cancels a false alarm)
         -> HTTP POST over SIM800L GPRS  (retries)  -> if that fails: SMS backup
         -> optional Wi-Fi fallback for demo day (phone hotspot)

  Board: "ESP32 Dev Module" in the Arduino IDE (Espressif ESP32 core 2.x or 3.x). No extra libraries.
  Open the Serial Monitor at 115200 baud: it prints the live force so you can calibrate THRESHOLD_N.
*/
#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>

// ============================ CHANGE THESE ============================
#define DEVICE_ID        "RESQ-ESP32-001"        // must match the unit on the website (Sensor network)
#define DEVICE_TOKEN     ""                      // IOT_DEVICE_TOKEN on the server; empty while testing locally
#define SERVER_URL       "http://YOUR-PUBLIC-HOST/api/v1/iot/sim"   // see README: ngrok / cloud server (plain http for SIM800L)
#define SIM_APN          "airtelgprs.com"        // Airtel: airtelgprs.com | Vi: www | BSNL: bsnlnet  (Jio does NOT work: SIM800L is 2G only)
#define SMS_BACKUP_TO    ""                      // e.g. "+9198XXXXXXXX": gets an SMS if the website cannot be reached
#define FIXED_LAT        12.8231                 // the car's demo location (no GPS on this build)
#define FIXED_LNG        80.0442
#define THRESHOLD_N      40.0                    // crash force limit in newtons: calibrate with hand hits (see Serial Monitor)
#define CANCEL_WINDOW_S  10                      // seconds the driver has to press "I'm OK" (0 = send immediately)
#define USE_WIFI_FALLBACK 0                      // 1 = also try Wi-Fi if the SIM fails (demo-day backup)
#define WIFI_SSID        "your-hotspot"
#define WIFI_PASS        "password"
#define WIFI_SERVER_URL  "http://192.168.43.100:8000/api/v1/iot/sim"  // laptop IP on the hotspot; run uvicorn --host 0.0.0.0

// ============================ PINS (ESP32 DevKit V1) ============================
#define PIN_FSR      34   // FSR divider output (ADC1). 3V3 -> FSR -> GPIO34 -> 10k -> GND
#define PIN_BUZZER   25   // active buzzer (+) through a transistor if it draws > 20 mA
#define PIN_LED      2    // on-board LED
#define PIN_OK_BTN   27   // "I'm OK" push button to GND (internal pull-up)
#define PIN_SIM_RX   16   // ESP32 RX2 <- SIM800L TXD
#define PIN_SIM_TX   17   // ESP32 TX2 -> SIM800L RXD (use a 10k/20k divider: SIM800L RX is 2.8 V)
const float R_FIXED = 10000.0;   // the resistor in the FSR divider (ohms)

// ============================ TUNING ============================
const uint16_t SAMPLE_US = 2000;         // 500 samples/s: a hand hit lasts only ~20-80 ms
const uint8_t  CONFIRM_SAMPLES = 3;      // over the limit for >= 3 samples (6 ms) to ignore electrical spikes
const uint32_t COOLDOWN_MS = 30000;      // one alert per 30 s
const uint32_t HEARTBEAT_MS = 120000;    // "I'm alive" + signal strength every 2 min (no incident)
const uint8_t  HTTP_RETRIES = 3;

HardwareSerial SIM(2);
uint32_t lastAlert = 0, lastBeat = 0, lastPrint = 0;
uint8_t over = 0;
float peakN = 0; int peakRaw = 0;

// ---------- force estimate from the FSR divider (Interlink FSR-402 style curve; approximate) ----------
float forceFromAdc(int raw) {
  if (raw < 20) return 0;
  float v = raw * 3.3f / 4095.0f;
  float rFsr = R_FIXED * (3.3f - v) / v;          // ohms
  float microSiemens = 1e6f / rFsr;
  return microSiemens <= 1000 ? microSiemens / 80.0f : (microSiemens - 1000) / 30.0f;
}

// ---------- SIM800L AT helpers ----------
String atRead(uint32_t ms) {
  String r; uint32_t t = millis();
  while (millis() - t < ms) { while (SIM.available()) r += (char)SIM.read(); delay(5); }
  return r;
}
String at(const String& cmd, uint32_t ms = 1500, const char* expect = "OK") {
  while (SIM.available()) SIM.read();
  SIM.println(cmd);
  String r; uint32_t t = millis();
  while (millis() - t < ms) {
    while (SIM.available()) r += (char)SIM.read();
    if (r.indexOf(expect) >= 0 || r.indexOf("ERROR") >= 0) break;
    delay(5);
  }
  Serial.printf("  > %s\n  < %s\n", cmd.c_str(), r.c_str());
  return r;
}
int signalQuality() {                              // AT+CSQ -> 0..31 (99 = unknown)
  String r = at("AT+CSQ");
  int i = r.indexOf("+CSQ: ");
  return i < 0 ? 99 : r.substring(i + 6).toInt();
}
bool simReady() {
  if (at("AT").indexOf("OK") < 0) return false;
  at("ATE0");
  for (int i = 0; i < 20; i++) {                  // wait up to 20 s for network registration
    String r = at("AT+CREG?");
    if (r.indexOf(",1") >= 0 || r.indexOf(",5") >= 0) return true;
    delay(1000);
  }
  return false;
}
bool gprsUp() {
  at("AT+SAPBR=3,1,\"Contype\",\"GPRS\"");
  at(String("AT+SAPBR=3,1,\"APN\",\"") + SIM_APN + "\"");
  at("AT+SAPBR=1,1", 12000);                       // "ERROR" here usually means it is already open
  return at("AT+SAPBR=2,1").indexOf("+SAPBR: 1,1") >= 0;
}

// POST form data over GPRS. Returns the server's reply line ("OK <reading> <incident> <status>") or "".
String simPost(const String& body) {
  if (!simReady() || !gprsUp()) return "";
  at("AT+HTTPTERM");
  if (at("AT+HTTPINIT").indexOf("OK") < 0) return "";
  at("AT+HTTPPARA=\"CID\",1");
  at(String("AT+HTTPPARA=\"URL\",\"") + SERVER_URL + "\"");
  at("AT+HTTPPARA=\"CONTENT\",\"application/x-www-form-urlencoded\"");
  if (String(SERVER_URL).startsWith("https")) at("AT+HTTPSSL=1");   // old TLS only: prefer plain http (README)
  if (at("AT+HTTPDATA=" + String(body.length()) + ",10000", 3000, "DOWNLOAD").indexOf("DOWNLOAD") < 0) return "";
  SIM.print(body); atRead(1000);
  String r = at("AT+HTTPACTION=1", 30000, "+HTTPACTION:");
  if (r.indexOf("+HTTPACTION:") < 0) r += atRead(30000);
  int st = 0, i = r.indexOf("+HTTPACTION: 1,");
  if (i >= 0) st = r.substring(i + 15).toInt();
  String reply;
  if (st == 200 || st == 201) {
    String rd = at("AT+HTTPREAD", 3000);
    int k = rd.indexOf("OK ");
    reply = k >= 0 ? rd.substring(k, rd.indexOf('\n', k)) : "OK";
    reply.trim();
  }
  at("AT+HTTPTERM");
  Serial.printf("HTTP status %d  reply: %s\n", st, reply.c_str());
  return reply;
}

bool smsBackup(const String& text) {
  if (strlen(SMS_BACKUP_TO) == 0 || !simReady()) return false;
  at("AT+CMGF=1");
  if (at(String("AT+CMGS=\"") + SMS_BACKUP_TO + "\"", 3000, ">").indexOf(">") < 0) return false;
  SIM.print(text); SIM.write(0x1A);
  return atRead(10000).indexOf("+CMGS") >= 0;
}

String wifiPost(const String& body) {
#if USE_WIFI_FALLBACK
  if (WiFi.status() != WL_CONNECTED) {
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    for (int i = 0; i < 20 && WiFi.status() != WL_CONNECTED; i++) delay(500);
  }
  if (WiFi.status() != WL_CONNECTED) return "";
  HTTPClient http; http.begin(WIFI_SERVER_URL); http.setTimeout(8000);
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");
  int st = http.POST(body); String r = http.getString(); http.end();
  Serial.printf("Wi-Fi HTTP %d %s\n", st, r.c_str());
  return (st == 200 || st == 201) ? r : "";
#else
  return "";
#endif
}

String form(const char* type, float forceN, int raw, int csq, const String& eventId) {
  String b = "id=" DEVICE_ID "&ty=" + String(type) + "&raw=" + raw + "&csq=" + csq + "&fw=car-1.0";
  if (eventId.length()) b += "&e=" + eventId;
  if (forceN > 0) b += "&f=" + String(forceN, 1) + "&t=" + String(THRESHOLD_N, 1);
  b += "&lat=" + String(FIXED_LAT, 6) + "&lng=" + String(FIXED_LNG, 6);
  if (strlen(DEVICE_TOKEN)) b += "&k=" DEVICE_TOKEN;
  return b;
}

// "I'm OK" window: beep; a button press cancels. Returns true if the alert should be sent.
bool cancelWindow() {
  if (CANCEL_WINDOW_S == 0) return true;
  Serial.printf("CRASH detected. Sending in %d s unless \"I'm OK\" is pressed...\n", CANCEL_WINDOW_S);
  for (int i = 0; i < CANCEL_WINDOW_S * 10; i++) {
    digitalWrite(PIN_BUZZER, (i % 5) < 2); digitalWrite(PIN_LED, (i % 5) < 2);
    if (digitalRead(PIN_OK_BTN) == LOW) {
      digitalWrite(PIN_BUZZER, LOW); digitalWrite(PIN_LED, LOW);
      Serial.println("Cancelled by the driver (I'm OK). Nothing sent.");
      return false;
    }
    delay(100);
  }
  digitalWrite(PIN_BUZZER, LOW);
  return true;
}

void sendCrash(float forceN, int raw) {
  String eventId = String(DEVICE_ID) + ":" + String((uint32_t)esp_random(), HEX);   // same id on every retry: no duplicate incidents
  int csq = signalQuality();
  String body = form("crash", forceN, raw, csq, eventId);
  String reply;
  for (int a = 1; a <= HTTP_RETRIES && reply.length() == 0; a++) {
    Serial.printf("Sending crash alert over SIM (attempt %d)...\n", a);
    reply = simPost(body);
    if (!reply.length()) delay(3000);
  }
  if (!reply.length()) reply = wifiPost(body);
  if (reply.length()) {
    Serial.println("Delivered to RESQ.AI: " + reply);
    for (int i = 0; i < 3; i++) { digitalWrite(PIN_LED, HIGH); delay(150); digitalWrite(PIN_LED, LOW); delay(150); }
  } else {
    bool ok = smsBackup(String("RESQ.AI CRASH ALERT ") + DEVICE_ID + ": force " + String(forceN, 1) + " N (limit " +
                        String(THRESHOLD_N, 0) + " N). Location https://maps.google.com/?q=" + String(FIXED_LAT, 5) + "," + String(FIXED_LNG, 5));
    Serial.println(ok ? "Website unreachable: SMS backup sent." : "Website unreachable and no SMS backup configured.");
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_BUZZER, OUTPUT); pinMode(PIN_LED, OUTPUT); pinMode(PIN_OK_BTN, INPUT_PULLUP);
  analogReadResolution(12);
  analogSetPinAttenuation(PIN_FSR, ADC_11db);      // full 0-3.3 V range
  SIM.begin(9600, SERIAL_8N1, PIN_SIM_RX, PIN_SIM_TX);
  delay(3000);
  Serial.println("\nRESQ.AI in-car unit " DEVICE_ID);
  Serial.printf("Threshold %.1f N. Hit the sensor by hand and watch the force values to calibrate.\n", THRESHOLD_N);
  Serial.printf("SIM: %s, signal %d/31\n", simReady() ? "registered" : "NOT registered (check SIM, antenna, power)", signalQuality());
}

void loop() {
  static uint32_t lastSample = 0;
  if (micros() - lastSample < SAMPLE_US) return;
  lastSample = micros();

  int raw = analogRead(PIN_FSR);
  float f = forceFromAdc(raw);

  if (millis() - lastPrint > 250) {                 // live value for calibration
    lastPrint = millis();
    Serial.printf("force %.1f N  (ADC %d)%s\n", f, raw, f >= THRESHOLD_N ? "  <-- over limit" : "");
  }

  if (f >= THRESHOLD_N) {
    if (++over == 1) { peakN = 0; peakRaw = 0; }
    if (f > peakN) { peakN = f; peakRaw = raw; }
  } else if (over > 0) {
    bool qualified = over >= CONFIRM_SAMPLES && millis() - lastAlert > COOLDOWN_MS;
    over = 0;
    if (qualified) {
      lastAlert = millis();
      Serial.printf("Impact: peak %.1f N (ADC %d), limit %.1f N\n", peakN, peakRaw, THRESHOLD_N);
      if (cancelWindow()) sendCrash(peakN, peakRaw);
    }
  }

  if (HEARTBEAT_MS > 0 && millis() - lastBeat > HEARTBEAT_MS && over == 0) {  // keeps the unit "Online"; set HEARTBEAT_MS 0 to skip
    lastBeat = millis();
    String r = simPost(form("hb", 0, raw, signalQuality(), ""));
    if (!r.length()) wifiPost(form("hb", 0, raw, 99, ""));
  }
}
