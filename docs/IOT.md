# IoT / ESP32

Firmware: `iot/` (PlatformIO, Arduino core, espressif32 7.1.3). Version 2.0.0.

## Pin plan (prototype — verify against your board and modules)

| Module | ESP32 pin | Notes |
|---|---|---|
| MPU6050 | SDA 21, SCL 22 | I²C 0x68 |
| MQ-2 AO | GPIO34 (ADC1) | 5 V module: voltage divider to ≤3.3 V |
| Water-level AO | GPIO35 (ADC1) | power from 3.3 V or divide output |
| FSR (SOS pad) | GPIO32 (ADC1) | divider with ~10 kΩ to GND |
| DHT22 | GPIO4 | kept from v1 (temperature for fire detection) |
| SIM800L | RX2 16 ← TXD, TX2 17 → RXD | 3.7–4.2 V, 2 A bursts; RXD is 2.8 V logic |

Changed from v1: MQ-2 moved from GPIO32 to GPIO34 to follow the project pin plan.

## Detection (`hazard_detector.cpp`)

| Event | Rule | Sent as |
|---|---|---|
| Impact | filtered |a| ≥ 5 g or dynamic ≥ 1.8 g for 3 consecutive samples | `ACCIDENT` |
| Smoke/gas | MQ-2 ADC delta over clean-air baseline ≥ 800 after 5 s at ≥ 350; warm-up + calibration required | `FIRE` |
| Temperature | ≥ 60 °C after 10 s at ≥ 50 °C | `FIRE` |
| Water | ADC ≥ 2200 after 10 s at ≥ 1200; hysteresis 150 | `FLOOD` |
| SOS pad | FSR ≥ 2500 held 3 s; re-arms on release; never suppressed by cooldown | `SOS` |

Thresholds are raw ADC counts, not ppm or cm. Calibrate with the real modules. Warnings never create incidents; only `alert_qualified=true` events do.

## Delivery

- Each payload gets `event_id = DEVICE_ID:bootCount:seq` (boot count persisted in NVS).
- **Alerts** go to a persistent NVS ring (`alert_store.h`, 8 slots) before sending and are removed **only** after a 2xx response containing `reading_id`. They survive reboots and power loss. If the store is full, the oldest pending alert is overwritten and logged.
- **Telemetry** (every 30 s) uses a RAM queue and may be dropped when offline.
- Transport: Wi-Fi with exponential reconnect. If Wi-Fi is down and GPRS is enabled, alerts go over SIM800L ([GSM_INTEGRATION.md](GSM_INTEGRATION.md)). Telemetry never uses GPRS.
- Retries: bounded exponential backoff (1 s → 60 s). The backend deduplicates by `event_id`, so a retry after a lost acknowledgement returns `DUPLICATE` with the original incident.

## Backend contract

`POST /api/v1/iot/events`, header `Authorization: Bearer <IOT_DEVICE_TOKEN>`. Location: firmware `FIXED_LATITUDE/LONGITUDE` if set, otherwise the location an admin registered for the device (Admin → Devices). Alerts without any location are stored but rejected for incident creation (`REJECTED_NO_LOCATION`).

## Tests

Host (g++): `test/host/hazard_detector_test.cpp` (gas, temperature, motion, water, SOS, event-id format), `test/host/alert_store_test.cpp` (order, survives "reboot", ack-only removal, overflow). Backend: `testing/test_iot.py`. **The firmware was not compiled or run on hardware in this build environment**; CI runs `pio run`.

## Setup

```bash
cd iot && cp include/secrets.example.h include/secrets.h   # Wi-Fi, API URL, device token, APN
pio run -t upload && pio device monitor
```
Register the device and its installed location in Admin → Devices.
