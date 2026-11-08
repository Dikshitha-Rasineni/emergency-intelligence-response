# Testing

## Run

```bash
cd backend
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/resq_ai_test python -m pytest ../testing -q
```
The suite drops and recreates the test database, runs all migrations, seeds demo data, disables AI providers and points routing at a closed port, so **no external calls and no real alerts** are made. Result at release: **60 passed** (~8 s).

## Coverage against the scenario list

| # | Scenario | Test |
|---|---|---|
| 1 | Road accident without image | `test_report_returns_token_and_rule_assessment` |
| 3, 21 | Fire with image | `test_fire_image_corroborates_and_routes` (mocked vision) |
| 6 | ESP32 accident event | `test_sensor_and_citizen_converge_into_one_incident` |
| 7 / 8 | Sensor fire / flood | `test_qualified_fire_creates_incident_routed_to_fire`, `test_qualified_flood_routes_to_disaster` |
| 9, 34 | Mixed hazards | `test_mixed_accident_fire_activates_all_three` |
| 10–13 | te / ta / hi / en | `test_multilingual_user_language_and_english_control_room` |
| 14, 16 | Code-switched, transliterated | `test_code_switched_and_transliterated` |
| 17 | Uncertain language | `test_uncertain_language_low_confidence` |
| 18 | Translation/LLM failure | `test_llm_failure_falls_back` |
| 23, 29 | Irrelevant / contradictory image | `test_irrelevant_or_contradictory_image_needs_review` |
| 24 | Duplicate image | `test_exif_stripped_and_duplicate_detected` |
| 27 | Vision timeout | `test_vision_failure_marks_failed_not_blocking` |
| 28 | Invalid / oversized upload | `test_invalid_and_oversized_files_rejected` |
| 30–33, 35 | Routing policy | `test_routing_and_access.py` |
| 36 | Unauthorized access | `test_unrouted_department_cannot_see_incident` |
| 37 | Field filtering | `test_field_level_filtering` |
| 38 | Normal telemetry | `test_routine_telemetry_never_creates_incident` |
| 39, 47 | Duplicate / reboot replay | `test_duplicate_event_is_idempotent` + `alert_store_test.cpp` |
| 43 | Invalid / missing location | `test_registered_location_used_and_missing_location_rejected`, `test_invalid_coordinates_rejected` |
| — | Routing unavailable, no fabrication | `test_route_unavailable_is_not_fabricated` |
| — | Notification lifecycle, escalation, WebSocket | `test_acknowledge_status_and_citizen_updates`, `test_notification_escalates_after_deadline`, `test_websocket_pushes_to_routed_department_only` |
| — | Provider wiring | `test_llm_provider.py` |

## Not covered automatically

Real LLM/vision quality (needs a model and an evaluation set), browser speech recognition, Wi-Fi/GPRS failure on hardware (40–42), database outage (45: the API returns an error; no queueing layer), and physical sensor calibration. The UI was checked with a scripted Playwright run (report in Telugu on a phone viewport → track → fire control room → acknowledge → admin) with no page errors.

## Firmware host tests

```bash
cd iot
g++ -std=c++17 -Wall -Wextra -I include src/hazard_detector.cpp test/host/hazard_detector_test.cpp -o /tmp/h && /tmp/h
g++ -std=c++17 -Wall -Wextra -I include test/host/alert_store_test.cpp -o /tmp/a && /tmp/a
```
