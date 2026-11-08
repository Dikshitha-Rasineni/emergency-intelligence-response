# Implementation status (v2.0, 2026-11-03)

Legend: **Tested** = implemented and covered by automated tests that pass · **Implemented** = built and exercised manually, no automated test · **Partial** = works with stated limits · **Not verified** = code written but could not be run in the build environment · **Planned** = not built.

Automated results at release: backend `pytest testing` → **60 passed** (PostgreSQL 16 + PostGIS 3.4). Frontend `tsc` + `vite build` clean; Playwright run of the citizen → control-room → admin flow with **0 page errors**. Firmware host tests (`hazard_detector_test`, `alert_store_test`) pass with g++. The ESP32 firmware itself was **not compiled** here (PlatformIO toolchain download blocked) — CI builds it.

| Area | Capability | Status | Notes / evidence |
|---|---|---|---|
| Intake | Text report, instant rule-based assessment | Tested | `test_report_returns_token_and_rule_assessment` |
| Intake | Citizen tracking with private token | Tested | token hash stored; `test_tracking_requires_token` |
| Intake | Citizen cannot set priority (old slider) | Tested | `user_priority` ignored |
| Intake | "No confirmed emergency" instead of SAFE | Tested | `insufficient_evidence` flag |
| Language | Detection with confidence, mixed & romanised Telugu/Tamil/Hindi | Tested | script share + keyword list; romanised = low confidence |
| Language | Citizen guidance in en/te/ta/hi | Tested | Kannada/Malayalam detected, guidance falls back to English (flagged) |
| Language | Translations of UI + guidance | Partial | Written for this project; **not reviewed by native-speaking emergency professionals** |
| Language | English-only control-room output | Tested | LLM `english_summary`, or fact-based English summary when no LLM |
| Voice | Browser speech (Web Speech API, te-IN/ta-IN/hi-IN/en-IN) | Implemented | Browser support varies (Chrome/Edge best). Not testable headless |
| Voice | Server transcription fallback (Gemini / Whisper-compatible) | Not verified | Code path + endpoint exist; needs an API key |
| GenAI | Ollama / Gemini / OpenAI-compatible providers | Tested (mocked HTTP) | `think:false`, JSON mode, keep-alive verified in request payloads. **No real model was run** (downloads blocked) |
| GenAI | Hallucinated-number rejection, LLM failure fallback | Tested | `test_llm_hallucinated_numbers_are_rejected` |
| GenAI | Background LLM enrichment re-assesses incident | Tested | `test_background_llm_enrichment_updates_record` |
| GenAI | Qwen2.5-3B GGUF / llama.cpp | Partial | Supported via the `openai` provider pointed at `llama-server`; not run here |
| GenAI | Fine-tuning / LightGBM priority model | Planned | No training data exists; priority stays rule-based by design |
| Images | Upload, validation, EXIF stripping, duplicate & blur flags | Tested | `test_media.py` |
| Images | Vision model analysis + privacy filtering | Tested (mocked model) | identity/medical words removed; `injury_assessment` forced to "cannot be determined" |
| Images | Real vision model quality | Not verified | Recommended `qwen2.5vl:3b` (Ollama) or Gemini Flash; evaluate on your own image set |
| Priority | Versioned rules with evidence + human override + audit | Tested | rules-v2 |
| Routing | Deterministic department policy with reasons (incl. exclusions) | Tested | scenarios 30–35 |
| Routing | Field-level filtering per department | Tested | scenario 37 |
| Access | JWT auth, roles, unrouted incidents hidden (404) | Tested | scenario 36 |
| Notifications | CREATED→PENDING→SENT→DELIVERED→ACKNOWLEDGED / ESCALATED / CANCELLED | Tested | DELIVERED only on client receipt |
| Notifications | SMS / push channels | Planned | Channel column exists; no provider integrated |
| Real-time | WebSocket push per department + reconnect + polling fallback | Tested (backend), Implemented (UI) | |
| Geo | PostGIS nearby search (GiST index, triggers) | Tested | |
| Geo | Real routes (OSRM / Amazon Location), no fabricated fallback | Tested (unavailable path) | OSRM success path **not verified** here (no outbound network) |
| Geo | OpenStreetMap live facility lookup | Implemented | Off by default in tests; labelled "community data, unverified" |
| Geo | Google Maps | Planned | OSM + OSRM chosen to avoid a second paid provider; Amazon Location kept as option |
| RAG | Admin ingestion, approval, full-text retrieval with citations | Tested | Extractive only. **No documents shipped** — add official guidance |
| RAG | BGE-M3 embeddings / pgvector | Planned | pgvector available; model not bundled |
| Copilot | Department briefs: facts vs suggestions, sources | Tested | Rule-based suggestions, no LLM |
| IoT | Idempotent ingestion, no incident from unqualified/simulated/telemetry | Tested | fixes audit bug #1 |
| IoT | Device auth (shared token), registered device location | Tested | |
| IoT | Sensor + citizen reports merge into one incident | Tested | ≤300 m, ≤20 min, compatible category |
| Firmware | MPU6050 / MQ-2 / DHT22 logic | Tested (host) | existing, kept |
| Firmware | Water-level + FSR SOS pad logic | Tested (host) | thresholds are raw ADC: **calibrate on hardware** |
| Firmware | Persistent NVS alert queue, event IDs, ack-only removal | Tested (host logic) | NVS adapter not run on device |
| Firmware | SIM800L GPRS fallback | Not verified | Plain HTTP only (SIM800L has no modern TLS); off by default |
| Firmware | Physical hardware test | Not verified | No hardware available |
| Frontend | Landing, citizen report/track, control rooms, admin, i18n | Implemented | Screenshots in `docs/screenshots/` |
| Deploy | Dockerfile + docker-compose (PostGIS, optional Ollama) | Not verified | Docker not available in the build environment |
| Data | Demo seed | Implemented | Fictional facilities flagged `DEMO_SEED`, no phones, availability UNKNOWN |
