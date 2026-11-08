# RESQ.AI ESP32 firmware

Arduino Core for ESP32 firmware built with PlatformIO. The ESP32 reports preliminary sensor observations; the backend retains responsibility for incident assessment. The project `Hardware/` directory was empty, so this implementation extends the existing `emergency-intelligence-response-main/iot/` firmware.

## Hardware and pin map

The existing firmware notes document an ESP32-D0WD-V3 and a *provisional* ESP32 DevKit V1 pin map. The actual carrier board and connected sensor wiring have not been inspected. Verify the board pinout and wiring before powering anything. Change assignments only in `include/config.h`.

| Part | ESP32 connection | Notes |
|---|---|---|
| MPU6050 SDA | GPIO21 | I2C, 3.3 V logic |
| MPU6050 SCL | GPIO22 | I2C, 3.3 V logic |
| MPU6050 VCC/GND | 3V3/GND | Confirm breakout supports this supply |
| MQ-2 AO | GPIO32 | ADC1; add divider/level conditioning so ADC input never exceeds 3.3 V (prefer margin below rail) |
| MQ-2 supply | Per module specification | MQ-2 heater modules commonly need 5 V and substantial warm-up; never feed 5 V AO directly to ESP32 |
| DHT22 DATA | GPIO4 | Add pull-up (typically 4.7–10 kΩ) if bare sensor; many modules include one |
| DHT22 VCC/GND | 3V3/GND | Confirm sensor variant and wiring |
| LED / buzzer | Disabled (`-1`) | Enable only after selecting safe pins and confirming driver/current requirements |

GPIO 21/22/32/4 are centralized defaults, not a claim that every ESP32 board uses the same accessible pins. No circuit diagram was present in `Hardware/`; PDF project notes list the sensors but do not define their detailed wiring. The old config also mentions FSR, sound, SIM800L, and a water probe; those are outside this firmware's active sensor scope.

## Setup

1. Install VS Code and the PlatformIO IDE extension, or install PlatformIO Core (`pio`).
2. From this directory, copy `include/secrets.example.h` to `include/secrets.h` and fill in local values. `secrets.h` is ignored by git.
3. Set `DEVICE_ID` and any verified sensor pins/thresholds in `include/config.h`.
4. Set a real installation latitude and longitude in `config.h` before API delivery. `0,0` is treated as unknown. No GPS exists in this build, so coordinates must be entered only for a stationary installation whose location is known. The current backend requires coordinates and has no unknown-location representation.
5. Configure `RESQ_API_BASE_URL` in `secrets.h` to a backend address reachable from the ESP32, e.g. `http://192.168.1.10:8000` on a trusted development LAN. Do not use `127.0.0.1` on the ESP32: that refers to the ESP32 itself.
6. Build: `pio run`.
7. Confirm COM port and upload: `pio run -t upload --upload-port COM11` (the CP210x was previously observed on COM11; recheck before use).
8. Serial monitor: `pio device monitor -p COM11 -b 115200`.

### Secrets and transport

Never commit `include/secrets.h`. The repository's existing backend route currently does **not** implement device authentication; a Bearer token may be configured by the client but will not be verified by that backend. Do not treat that as authentication. For production, add server-side per-device authentication and deploy TLS first. For HTTPS, supply the server's trusted root CA PEM in `RESQ_ROOT_CA`; certificate verification is mandatory, and an empty CA causes HTTPS delivery to be refused. HTTP is limited to explicitly permitted local/private development URLs by `ALLOW_INSECURE_LOCAL_HTTP`; disable it for a production build.

## Measurement and alert behavior

- MPU6050 acceleration values are m/s². The filtered acceleration magnitude in G includes gravity; `dynamicAccelerationG` subtracts 1 g from the smoothed magnitude as a basic movement indicator, not full orientation-aware gravity compensation. Vibration RMS is measured from short dynamic-magnitude windows. An incident candidate requires 3 consecutive samples over the configured total/dynamic threshold.
- MQ-2 reports filtered raw ADC counts only. Startup baseline is averaged after boot and the sensor warm-up; warning/critical thresholds are ADC deltas from that baseline. This is a relative signal, **not verified ppm**. Do not set the backend's `smoke_level` field from it. Calibrate in clean air after the manufacturer's recommended initial burn-in and per-use warm-up; set `MQ2_WARMUP_MS`, ADC divider and delta thresholds from the actual module and installation.
- DHT22 temperature is °C and humidity is %RH. Reads are spaced at 2.5 s; failed or implausible values remain unavailable and are omitted.
- Hazard states are `normal`, `warning`, `critical`, and `sensor_fault`. Gas and temperature need persistence; hysteresis clears warning state. Motion requires consecutive samples. One notification is emitted for each persistent episode, with a cooldown; recovery re-arms a later event.
- `ACCIDENT` and `FIRE` event types can cause the current backend service to create an incident. Therefore only qualified critical conditions are sent with those event types. Warnings remain local and are visible in serial status. A transmitted `TELEMETRY` updates stored readings without automatically claiming a disaster.
- Timestamps are omitted because the current backend stamps receipt time and there is no configured NTP clock. GPS/location is not fabricated.

## Backend contract

The backend route is `POST /api/v1/iot/events`. This implementation adds backward-compatible optional fields for humidity, MQ-2 raw/filtered/baseline ADC, MPU acceleration and gyro values, sensor availability, Wi-Fi state, firmware version, uptime, and qualified alert metadata. The firmware requires a response containing `reading_id` for acknowledgement. It sends raw MQ-2 counts as `mq2_raw_adc`, never as `smoke_level` ppm. It sends passive acceleration under `acceleration_magnitude_g`; legacy `impact` is included only with a locally qualified motion alert, so a single telemetry sample cannot trigger the backend's incident threshold. Routine readings set `alert_qualified=false`; qualified `ACCIDENT`/`FIRE` alerts include sensor, observed value, configured threshold, unit, severity and reason. No water sensor is configured. The backend has no device registration flow and this route has no authentication dependency.

Before deploying the firmware, apply additive database migrations from the backend directory: `python -m alembic upgrade head`. They add nullable sensor/alert/health columns; `alert_qualified` and `simulated` default to false for existing readings.

The response `incident_id` is logged when returned. The backend creates incidents for explicit qualified event types, then uses its existing incident assessment workflow. The API still requires real coordinates and does not verify the optional Bearer header; no device authentication is enforced server-side.

## Offline operation and simulation

Sensor acquisition runs on the Arduino loop. A separate FreeRTOS network worker manages Wi-Fi with exponential reconnect delays and performs HTTP with 5 s connect/request timeouts. Telemetry and alerts are held in bounded RAM queues (6 routine, 2 priority); priority jobs drain first. Queue contents are lost at reboot, and overflow/drop is logged. API failures requeue once per attempt with a delay; there is no unbounded retry or RAM growth. Sensor acquisition continues during network timeouts.

For no-hardware checks, set `SIMULATION_MODE=true` in `config.h`. This produces explicitly identified deterministic local mock values and a periodic possible-motion episode. By default simulated jobs are consumed locally and never uploaded (`ALLOW_SIMULATION_UPLOAD=false`). If enabling upload for a test backend, the API stores `simulated=true` and will never create incidents from those records. Simulation does not validate sensor electrical behavior.

## Validation and troubleshooting

- Build: `pio run` from `iot/`. This validates compilation only; it does not validate hardware, Wi-Fi, API delivery, or threshold suitability.
- Host logic test (MinGW/GCC): `g++ -std=c++17 -Wall -Wextra -I include src/hazard_detector.cpp test/host/hazard_detector_test.cpp -o .pio/hazard_detector_test.exe && .\.pio\hazard_detector_test.exe`. This covers threshold persistence, escalation, cooldown/latching, recovery, motion qualification and sensor-fault classification without hardware.
- Hardware checklist: confirm the board/USB serial port; inspect I2C address (`0x68`, or update config for an alternate MPU6050 address if needed); check DHT22 pull-up; measure MQ-2 analog voltage under worst case; wait through sensor warm-up/calibration; verify serial diagnostics and a known fixed location.
- Wi-Fi unavailable: sampling continues; check SSID/password and that the backend host is on the same reachable network. The network worker retries with a capped exponential schedule.
- No API acknowledgement: check the backend is listening on a LAN-reachable host (`--host 0.0.0.0` for local testing), path `/api/v1/iot/events`, firewall, configured coordinates, backend response and serial HTTP status. The existing app backend defaults to `127.0.0.1`; a remote ESP32 cannot reach that bind address.
- MQ-2 shows ADC values rather than ppm: expected. The new API persists raw and baseline ADC fields; a site-specific calibrated ppm conversion has not been implemented.
- No incident from warning: expected; only qualified critical episodes use `FIRE`/`ACCIDENT` event types.

## Test plan

1. Build with `pio run`.
2. Enable simulation and verify normal readings, a persisted warning, one qualified motion episode, recovery, and no upload by default.
3. On a bench, test each sensor separately, then with one sensor disconnected; invalid DHT values should be omitted and sensor status should show the fault.
4. Verify MQ-2 clean-air baseline, warning/critical deltas, hysteresis and recovery; never use raw ADC as ppm.
5. Apply the migration, then on a dedicated test backend/database and real configured testbed coordinates, verify HTTP 201 with `reading_id`, validation errors, 5xx/timeout behavior, Wi-Fi disconnect/reconnect, bounded queue behavior, telemetry persistence, and qualified server-created incident response. Simulated events are stored but never incident-triggering. The backend has no idempotency key, so do not run alert tests against an operational incident database.

## Known limitations

No attached circuit diagram, physical sensor wiring, GPS, NTP, backend device authentication, backend idempotency key, or OTA mechanism was found. The hardware status earlier showed a CP210x serial bridge on COM11, but no firmware upload or physical sensor validation has been performed in this implementation. Analog sensor disconnection cannot be conclusively inferred from `analogRead` alone; inspect MQ-2 wiring and its ADC range during commissioning. Use a dedicated test database for end-to-end tests.
