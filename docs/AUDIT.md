# RESQ.AI — Codebase Audit (before this round of changes)

Audit date: 2026-11-03. Source: `emergency-intelligence-response-main.zip` as supplied.
Each finding was checked against the code, not the README.

## Snapshot structure

```
emergency-intelligence-response-main/
├── resq.ai_emergency_response_platform/   # frontend: vanilla JS SPA (index.html + 2,300-line app.js) + server.py
└── emergency-intelligence-response-main/
    ├── backend/      FastAPI + SQLAlchemy + Alembic (5 migrations, 9 tables)
    ├── iot/          ESP32 PlatformIO firmware (MPU6050, MQ-2, DHT22; Wi-Fi only)
    ├── testing/      pytest suites (need PostgreSQL)
    ├── genai/ ml/ datasets/   README files only, no code
    └── docs/
```

## Feature status

| Area | Feature | Status | Evidence |
|---|---|---|---|
| Backend | Incident create/list/get/patch | IMPLEMENTED | `routes/incidents.py`, `incident_service.py` |
| Backend | Authentication / authorization | **NOT STARTED** | No auth dependency on any route; `users` table has no password |
| Backend | Pagination | PARTIALLY | `limit` only, no offset, no cap |
| Backend | Structured errors | PARTIALLY | `AppException` handler exists; most routes raise plain HTTPException |
| Backend | Audit log | NOT STARTED | — |
| Backend | Rate limiting | NOT STARTED | — |
| AI | LLM extraction | IMPLEMENTED BUT NOT VERIFIED | Ollama `qwen3:4b`, 4 s timeout. Qwen3 "thinking" is on by default, so most calls time out and silently use regex |
| AI | Rule-based fallback | IMPLEMENTED | `LanguageService` keyword/regex parser |
| AI | Confidence scores | **MISLEADING** | Fallback hard-codes 0.95, higher than the LLM's hard-coded 0.92 |
| AI | Qwen2.5-3B / llama.cpp / GGUF | NOT STARTED | Appears only in a draw.io diagram |
| AI | Vision / image analysis | NOT STARTED | No upload endpoint, no vision model |
| AI | Voice / speech-to-text | NOT STARTED | — |
| AI | RAG / embeddings / vector search | NOT STARTED | — |
| AI | Fine-tuning / ML training | NOT STARTED | `ml/`, `genai/`, `datasets/` are README-only |
| Language | Script-based detection (te/ta/hi/kn/ml/en) | IMPLEMENTED | Unicode-range detection; no confidence, no transliteration |
| Language | Localized precautions | IMPLEMENTED | Hard-coded strings; not reviewed by native speakers; no source attribution |
| Language | English control-room summary | IMPLEMENTED | `get_english_dispatch_summary` (template-based) |
| Language | Frontend i18n | NOT STARTED | UI strings are hard-coded English in `app.js` |
| Priority | Deterministic score 0–100 | IMPLEMENTED | `priority_service.py`; no version, no evidence provenance |
| Priority | Citizen slider | **MISLEADING** | Frontend slider; `user_priority` is just echoed back as the system score |
| Priority | "SAFE / LOW RISK" label | **MISLEADING** | Shown when the score is low, even without evidence |
| Routing | Department routing engine | NOT STARTED | Every incident goes to every dashboard; `role="ALL"` |
| Routing | Field-level filtering | NOT STARTED | Every role sees every field |
| Notifications | Delivery/ack tracking | NOT STARTED | `status` column on incident only |
| Real-time | WebSockets | NOT STARTED | Frontend polls |
| Geo | Nearby resources | IMPLEMENTED | DB (haversine ×1.25) + OSM Overpass live lookup |
| Geo | PostGIS | NOT STARTED | Plain float columns; no spatial index |
| Geo | Routing | PARTIALLY | Amazon Location → OSRM public → **fabricated curved polyline** labelled as a route |
| Geo | ETA | **MISLEADING** | Provider duration × 0.85 "siren factor"; fallback ETA invented from 40 km/h |
| Geo | Amazon Location map proxy | IMPLEMENTED BUT NOT VERIFIED | Needs AWS credentials |
| Data | Seed resources | **MISLEADING** | Real hospital names with invented bed counts, phone numbers and "Alpha Surgical Team On Duty" |
| Dashboard | System telemetry | **MISLEADING** | Hard-coded strings ("PostgreSQL 17 Live", "GIS Road-Tortuosity Matrix Active") |
| IoT | ESP32 sensor sampling (MPU6050, MQ-2, DHT22) | IMPLEMENTED BUT NOT VERIFIED ON HARDWARE | Good persistence/hysteresis logic, host tests pass |
| IoT | Water-level sensor, FSR | NOT STARTED | — |
| IoT | SIM800L GSM/GPRS | NOT STARTED | — |
| IoT | Offline queue | PARTIALLY | 8-slot RAM queue; lost on reboot |
| IoT | Unique event IDs / server idempotency | NOT STARTED | Retries can create duplicate incidents |
| IoT | Device authentication | NOT STARTED | Firmware sends a token; backend ignores it |
| Frontend | Citizen / hospital / police / fire / admin views | PARTIALLY | One page with a role switcher; anyone can open any role |
| Frontend | Image upload, voice input | NOT STARTED | — |
| Frontend | Landing page | NOT STARTED | — |
| Infra | Docker | NOT STARTED | — |
| Infra | CI | IMPLEMENTED | GitHub Actions: backend tests on Postgres, firmware build |

## Critical bugs and blockers (re-checked against source)

1. **IoT false-accident path (confirmed).** `iot_service.py` creates an incident whenever `event_type == "ACCIDENT"`, even when `alert_qualified` is false. Any client posting `event_type: "ACCIDENT"` creates an incident. There is also no idempotency key, so a firmware retry after a lost response creates a duplicate incident.
2. **Frontend false success (confirmed).** `app.js createIncident()` catches any backend error and returns a locally built object `INC-LOCAL` with a computed priority. The citizen sees a submitted report that was never stored.
3. **No authorization (confirmed).** Every endpoint is public, including PATCH of incident status and the dashboards.
4. **Fabricated route geometry.** The routing fallback draws a sine-curved line and returns it as a route with an ETA.
5. **LLM effectively disabled.** A 4 s timeout plus Qwen3 thinking mode means extraction is almost always the regex path, while the UI says "Ollama / Qwen".
6. **Invented operational data.** Seed availability and telemetry strings look real but aren't.
7. **Duplicate route registration.** Incident routes are mounted at `/api/v1`, `/api` and `/`, so `/incidents` at the root shadows the SPA paths.

## UI/UX deficiencies

- One crowded page with a role switcher instead of authenticated role areas.
- Inline styles everywhere; no component system; no i18n.
- "LOCAL ENGINE" badge and static-looking map fallbacks look like live operational data.
- No loading, empty or error states for most API calls.

## Target architecture (implemented in this round, see ARCHITECTURE.md)

Citizen (text/voice/images) and ESP32 events → FastAPI → **canonical incident** (one record per event; IoT events merge into nearby open incidents) → language detection → LLM extraction (Ollama / Gemini / OpenAI-compatible, rule fallback) → image analysis in the background (vision provider) → deterministic priority (versioned, with evidence) → deterministic department routing (with reasons) → per-department English reports with field filtering → notifications (state machine, ack, escalation) → WebSocket push to the authorized control rooms only. Citizen-facing guidance comes from the same record, in their language.
