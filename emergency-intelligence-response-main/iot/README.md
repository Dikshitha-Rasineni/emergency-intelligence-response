# RESQ.AI ESP32 vehicle/testbed unit

Prototype emergency-sensing firmware for Arduino Core on ESP32. **Not certified vehicle safety equipment; never connect it to airbags or other safety-critical automotive systems.**

## Verified before implementation

- Silicon Labs CP210x USB-to-UART adapter: **COM11**, present and opens at 115200.
- Non-flashing chip probe on COM11: **ESP32-D0WD-V3 rev 3.1**, MAC observed by esptool; exact carrier board and wiring remain unverified.
- `http://127.0.0.1:8000/health`: healthy, PostgreSQL connected.
- Ingestion route: `POST /api/v1/iot/events` (GET correctly returns 404).
- ESP32 must not use `127.0.0.1`; set `API_BASE_URL` to the backend PC LAN address and bind the backend to a reachable interface.

## Assumptions and wiring

PlatformIO target is `esp32dev`, based on the detected original ESP32 chip. GPIO assignments remain provisional:

| Component | GPIO / bus |
|---|---|
| MPU6050 SDA/SCL | GPIO21 / GPIO22, 3.3V I2C |
| DHT22 data | GPIO4 |
| FSR analog | GPIO34 (input-only) |
| Sound analog | GPIO35 (input-only) |
| MQ-2 analog | GPIO32 (must be 3.3V-safe) |
| Water analog | Not connected in supplied diagram |
| SOS switch | GPIO5 to GND, disabled by default |
| SIM800L TXD/RXD | GPIO17 / GPIO16 (UART2) |
| Buzzer + / GND | GPIO12 / GND |
| DIP switch | GPIO13, GPIO15, GPIO2, GPIO0 |

Confirm the exact board, voltage levels, sensor models, and wiring before powering the unit. MQ-2 modules commonly require level shifting for ESP32 ADC inputs.

The supplied diagram maps SIM800L UART to ESP32 GPIO16/17. SIM800L requires a separate regulated approximately 4.0 V supply with high-current burst capacity; do not power a bare module from the ESP32 3.3 V rail. Use common ground and appropriate UART level shifting. SIM800L provides GSM/GPRS, not GPS coordinates; use a separate GPS receiver if moving coordinates are required. The firmware currently probes the module with AT and continues to use Wi-Fi for the RESQ.AI HTTP API.

## Configure, build, and upload

1. Install VS Code + PlatformIO.
2. Copy `include/secrets.example.h` to `include/secrets.h` and set Wi-Fi credentials.
3. Edit `include/config.h`: device ID, reachable backend URL, genuine fixed coordinates, GPIOs, and calibrated conversion values.
4. Build: `pio run`.
5. After confirming the board/port, upload: `pio run -t upload --upload-port COM11`.
6. Monitor: `pio device monitor -p COM11 -b 115200`.

Default coordinates are invalid (`0,0`), so events are withheld until genuine GPS or installation coordinates are configured.

## API payload

The firmware sends the current backend contract to `POST /api/v1/iot/events`:

```json
{"device_id":"RESQ-ESP32-001","event_type":"TELEMETRY","temperature":31.5,"smoke_level":null,"water_level":2.5,"impact":0.15,"latitude":12.9,"longitude":80.1}
```

Periodic readings use `TELEMETRY`; qualified local events use `ACCIDENT`, `FIRE`, or `FLOOD`. Delivery is acknowledged only for a successful response containing `reading_id`; `incident_id` is logged when returned.

## Detection and limitations

- Impact is total acceleration magnitude in G, MPU6050 16G range, 21Hz filter, two qualifying 10ms samples, and 60s cooldown. Peaks beyond 16G may clip.
- Fire thresholds are 1500 estimated ppm or 60C. MQ-2 raw ADC is **not ppm** without hardware-specific calibration; supplied coefficients are placeholders.
- Flood threshold is 50cm using a configurable linear ADC conversion; calibrate for the actual sensor.
- DHT22 values are sampled at a supported interval and invalid readings are omitted.
- NVS stores up to eight JSON events, prioritizing emergencies. The current backend has no idempotency key, so duplicate delivery after a timeout cannot be ruled out.
- Multiple hazards can be sensed, but the current backend's ordered branch can represent only one incident type; this needs a backend enhancement.

## Backend correction

The Pydantic schema previously defaulted omitted `event_type` to `ACCIDENT`, while the database model defaults to `TELEMETRY`. The backend change in this work makes the request default `TELEMETRY`; firmware still sends it explicitly. No idempotency migration was added because the current contract has no idempotency field.

## Safe testing

Use a separate test backend/database and genuine test coordinates. Start with telemetry and inspect `reading_id`, then test threshold logic with controlled simulation/unit tests. Do not connect this prototype to a live control room. Physical sensor, Wi-Fi, PostgreSQL delivery, flashing, and exact wiring remain unverified until tested on the hardware.
