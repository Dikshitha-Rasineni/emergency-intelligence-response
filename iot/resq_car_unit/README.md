# RESQ.AI in-car crash unit (ESP32 + force sensor + SIM800L)

A force (pressure) sensor sits behind a fake dashboard in the car. Hitting it by hand simulates the crash.
The ESP32 reads it, compares it with the threshold, and sends the reading to the RESQ.AI website over the SIM card.
RESQ.AI then creates the incident, **GenAI writes each control room its brief**, and the nearest ambulance, patrol
and rescue tender are dispatched.

```
 hand hit -> FSR -> ESP32 (force in N, threshold, 10 s "I'm OK" window) -> SIM800L GPRS -> POST /api/v1/iot/sim
          -> RESQ.AI: incident + priority + routing + GenAI briefs (RAG) + auto-dispatch
          -> if the website cannot be reached: SMS backup to a phone number
```

## Parts

| Part | Notes |
|---|---|
| ESP32 DevKit V1 | "ESP32 Dev Module" in the Arduino IDE |
| FSR (e.g. FSR-402) + 10 kΩ resistor | the "crash" sensor behind the fake dashboard |
| SIM800L module + antenna | **2G only** |
| SIM card | **Airtel or Vi** (2G). **Jio does not work**: it has no 2G network |
| Power for SIM800L | 3.7–4.2 V that can give **2 A bursts**: a Li-ion cell or a buck converter set to 4.0 V, plus a 1000 µF capacitor. USB 5 V or the ESP32's 3.3 V pin will make it reboot |
| Active buzzer, push button | buzzer for the 10 s warning, button = "I'm OK" (cancel a false alarm) |

## Wiring

| From | To |
|---|---|
| 3V3 → FSR → **GPIO34** → 10 kΩ → GND | force sensor divider |
| SIM800L **TXD** | ESP32 **GPIO16** (RX2) |
| SIM800L **RXD** | ESP32 **GPIO17** (TX2) through a divider (10 kΩ / 20 kΩ): SIM800L RX is 2.8 V |
| SIM800L VCC / GND | 4.0 V supply / **common GND with the ESP32** |
| Buzzer + | **GPIO25** (through a transistor if it draws more than 20 mA) |
| Button | **GPIO27** to GND |

## Set up

1. Arduino IDE → Boards Manager → install **esp32 by Espressif**. Board: **ESP32 Dev Module**.
2. Open `resq_car_unit.ino` and edit the top block: `DEVICE_ID` (keep `RESQ-ESP32-001` to match the website),
   `SERVER_URL`, `SIM_APN` (Airtel `airtelgprs.com`, Vi `www`, BSNL `bsnlnet`), `SMS_BACKUP_TO`, `FIXED_LAT/LNG`.
3. Upload, open the Serial Monitor at **115200**. You should see `SIM: registered, signal 15/31` (10+ is fine).

## Calibrate the threshold (hand hit)

The Serial Monitor prints `force 3.2 N (ADC 410)` four times a second.

1. Press the sensor gently a few times: note the values (normal touch, e.g. 5–15 N).
2. Hit it like the demo "crash": note the peak (e.g. 50–80 N).
3. Set `THRESHOLD_N` between the two (e.g. **40**), re-upload. A gentle press must stay below it.

The force value is an estimate from the FSR's typical curve; it is consistent enough for a threshold, not a lab
measurement. Say so if asked.

## Make the website reachable from the SIM

The SIM card is on the internet; your laptop's `127.0.0.1` is not. Pick one:

- **ngrok (quickest).** Install ngrok, then `ngrok http 8000`. Put the forwarding address in `SERVER_URL` as
  **`http://`**`<your-subdomain>/api/v1/iot/sim`. The SIM800L cannot do modern HTTPS, so test the plain `http://`
  address first with the curl command below. If ngrok only answers on https, use the next option.
- **A small cloud server** (any VM with a public IP) running the backend on plain http, port 80 or 8000.
- **Demo-day backup, no SIM:** set `USE_WIFI_FALLBACK 1`, put the ESP32 and the laptop on the same phone hotspot,
  run the server with `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`, and set `WIFI_SERVER_URL` to the
  laptop's IP.

## Test the website without the hardware

This is exactly what the ESP32 sends:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/iot/sim \
  -d "id=RESQ-ESP32-001&e=test-$(date +%s)&ty=crash&f=62.5&t=40&raw=3350&csq=18&lat=12.8231&lng=80.0442"
```

Reply: `OK <reading_id> <incident_id> INCIDENT_CREATED`. Open the incident in the hospital control room: the sensor
banner shows *Sent over SIM · signal good (18/31)* and the GenAI brief describes the force-sensor crash.

## What it sends

`POST /api/v1/iot/sim` (form-encoded): `id` device, `e` event id (same on every retry, so retries never create a
second incident), `ty` `crash` or `hb` (heartbeat, never an incident), `f` force N, `t` threshold N, `raw` ADC,
`csq` signal 0–31, `lat`/`lng`, `fw`, `k` device token (when `IOT_DEVICE_TOKEN` is set on the server).
