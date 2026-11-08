# SIM800L GSM/GPRS fallback

**Status: written, not verified on hardware.** Disabled by default (`ENABLE_SIM800L=false`, `GPRS_ALLOW_PLAINTEXT=false` in `iot/include/config.h`).

## Why plain HTTP only

The SIM800L's built-in TLS supports only outdated protocol versions, and doing TLS on the ESP32 over a TinyGSM socket is unreliable on this module. The firmware therefore refuses GPRS unless you explicitly set `GPRS_ALLOW_PLAINTEXT=true`. Acceptable options:

1. A private APN / VPN from your operator, or
2. A small relay on a server you control that accepts HTTP on a non-public port from the SIM's IP range and forwards to the HTTPS API, or
3. Replace the SIM800L with a modem that supports TLS 1.2 (e.g. SIM7600/A7670).

The device token still travels in the header; treat GPRS plaintext as exposure of that token and rotate it if used over a public APN.

## Behaviour

- Used only for **alerts** when Wi-Fi is down (telemetry stays on Wi-Fi to save data).
- `GsmLink::ready()` waits for network registration (30 s) and attaches GPRS with `RESQ_GPRS_APN`; retries at most every `GPRS_RETRY_MS` (60 s).
- Payload has `"transport": "GPRS"`; the backend records it per reading and on the device.
- Delivery is acknowledged exactly like Wi-Fi (2xx + `reading_id`); unacknowledged alerts stay in flash.

## Hardware checklist

- 3.7–4.2 V supply able to deliver 2 A peaks (Li-ion cell or buck converter with large capacitor); never from the ESP32 3.3 V pin.
- Common ground; ESP32 TX → divider → SIM800L RXD (2.8 V).
- Antenna attached; SIM without PIN; 2G network availability in your area (many Indian operators are phasing out 2G: check coverage).
- SIM800L is not a GPS receiver; location comes from the registered device location.
