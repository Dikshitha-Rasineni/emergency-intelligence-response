# End-to-end workflow

## Path A: citizen report

1. Citizen opens `/report`, types or speaks (browser speech, else server STT), optionally adds photos, location is taken from GPS or a map pin (manual pins count as citizen-confirmed), category is optional.
2. `POST /incidents` (rate-limited): language detected with confidence; location resolved (GPS → verified; free-text geocode → approximate, unverified); rule-based extraction; duplicate check; incident + extraction stored; **assessment** (priority → routing → notifications → nearest resources → citizen guidance) committed; tracking token returned once.
3. Photos: `POST /incidents/{id}/media` with the token → validated, cleaned, stored; vision analysis in background → re-assessment.
4. Background: LLM extraction → validated → stored as a new extraction (method `llm`) → re-assessment → WebSocket push.
5. Control rooms receive `incident.notification` only if routed; dashboard confirms receipt (`DELIVERED`); operator acknowledges, updates status (optionally visible to the citizen), may override priority with a reason (audited).
6. Citizen `/track/{id}` polls every 8 s: status, priority with reasons, guidance in their language, departments and their acknowledgement state, public updates, nearby facilities.
7. Unacknowledged notifications past their deadline (2 min critical, 5 min otherwise) become `ESCALATED` and alert admins.

## Path B: ESP32 alert

1. Firmware detects a hazard using persistence + hysteresis (impact, smoke/gas ADC delta, temperature, water level, held SOS pad).
2. Alert payload with `event_id` (`DEVICE:boot:seq`) is written to NVS flash, then sent over Wi-Fi (or GPRS if enabled). Removed only on a 2xx acknowledgement with `reading_id`.
3. `POST /iot/events` (device token): reading stored; duplicates return the original acknowledgement; only `alert_qualified`, non-simulated, known-type events with a location (payload or registered device) create or join an incident.
4. From here it follows Path A step 2 onward (canonical incident, routing, notifications).
