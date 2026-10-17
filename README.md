# RESQ.AI — Emergency Intelligence & Response Support System

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-persistence-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)

RESQ.AI is an **Emergency Intelligence & Response Support System**. It converts citizen reports and IoT sensor events into structured incident data, explainable priority assessments, nearby-resource recommendations, GIS routing information, and role-specific response guidance.

> **Operational safety principle:** RESQ.AI is a decision-support system. It does not autonomously dispatch emergency services, diagnose patients, or replace an authorized responder. Human verification and operational authority remain essential.

## Contents

- [Documentation deep dives](#documentation-deep-dives)
- [Project scope](#project-scope)
- [What is implemented](#what-is-implemented)
- [System architecture](#system-architecture)
- [Operational workflows](#operational-workflows)
- [Technology stack](#technology-stack)
- [GenAI, NLP, transformer, and geospatial roles](#genai-nlp-transformer-and-geospatial-roles)
- [Repository structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Local setup](#local-setup)
- [Running the platform](#running-the-platform)
- [Configuration](#configuration)
- [Database and seed data](#database-and-seed-data)
- [API reference](#api-reference)
- [Example requests](#example-requests)
- [Roadmap and implementation status](#roadmap-and-implementation-status)
- [Academic relevance](#academic-relevance)
- [Team contributions](#team-contributions)
- [Testing and validation](#testing-and-validation)
- [Limitations and planned work](#limitations-and-planned-work)
- [Safety and data considerations](#safety-and-data-considerations)

## Documentation deep dives

- 📘 **[Comprehensive Architecture Guide](emergency-intelligence-response-main/docs/ARCHITECTURE.md)** — Multi-layer system topology, Amazon Location Service integration, edge hardware specs, mathematical ranking formulas, and component responsibilities.
- 🔄 **[End-to-End Operational Workflows](emergency-intelligence-response-main/docs/WORKFLOW.md)** — Sequence diagrams for citizen intake, automated IoT ingestion, hybrid AI processing, multi-agency dispatch, and fault-tolerance fallbacks.
- 📋 **[API Contract & Specifications](emergency-intelligence-response-main/docs/API_CONTRACT.md)** — Complete OpenAPI REST endpoints and Pydantic schemas.
- 🗄️ **[Relational Database Schema](emergency-intelligence-response-main/docs/DATABASE_SCHEMA.md)** — 9-table PostgreSQL 17 relational schema and Alembic migrations.
- ⚡ **[ESP32 IoT Firmware Guide](emergency-intelligence-response-main/iot/README.md)** — Embedded C++ firmware, sensor calibration, pin mappings, and non-volatile flash queue buffer.

## Project scope

The repository contains two cooperating applications:

1. `emergency-intelligence-response-main/` — the canonical FastAPI backend, SQLAlchemy models, Alembic migration, seed data, services, schemas, and tests.
2. `resq.ai_emergency_response_platform/` — a vanilla HTML/CSS/JavaScript operational interface and a small server wrapper that serves the interface together with the canonical backend.

The current implementation is centered on emergency reports in a Bengaluru-area demonstration dataset. The backend uses PostgreSQL for persistence and can optionally call a local Ollama model. If Ollama is unavailable, the application uses a deterministic parser so that report intake and basic decision support still work.

## What is implemented

- FastAPI application with canonical `/api/v1` routes and compatibility aliases under `/api` and selected root paths.
- Pydantic request validation for incidents, coordinates, casualties, AI requests, resource ranking, routes, and IoT telemetry.
- Incident creation pipeline: validation → hybrid AI extraction → deterministic priority/severity scoring → database persistence → response precautions and recommendations.
- PostgreSQL persistence through SQLAlchemy and an Alembic migration covering nine relational tables.
- Seeded emergency resources, availability records, responder nodes, users, and baseline incidents.
- Nearby-resource discovery using latitude/longitude distance calculations and road-distance estimates.
- Multi-factor resource ranking using proximity (40%), availability/capacity (30%), and emergency-type suitability (30%).
- **Amazon Location Service routing (`geo:CalculateRoute`)** with automatic secondary fallback to OSRM and tertiary local Haversine tortuosity model.
- **Amazon Location Service Map Proxy** serving vector tiles (`/tiles/{z}/{x}/{y}`), style descriptors (`/style.json`), glyphs, and sprites using backend IAM credentials.
- **ESP32 C++ firmware (`iot/`)** for DevKit V1 supporting MPU-6050, DHT22, MQ-2, FSR, Sound, SIM800L, and non-volatile flash memory (`Preferences` / NVS) offline queuing.
- Threshold-triggered automated incident synthesis for accident, fire, and flood telemetry.
- Hybrid AI decision support: optional Ollama JSON extraction plus deterministic keyword/regex fallback; non-diagnostic precautions; hospital, police, and fire response guidance.
- Five UI modes: citizen, hospital, police, fire, and admin/CAD with live MapLibre/Leaflet maps and route visualization.
- Comprehensive automated test suites: backend core tests (`test_backend.py`) and Amazon Location integration tests (`test_amazon_location.py`).

## System architecture

```mermaid
flowchart LR
    citizen["Citizen web report"] --> api["FastAPI Core API"]
    sensor["ESP32 IoT Node (MPU6050/DHT/MQ2)"] --> api
    api --> validate["Pydantic validation"]
    validate --> understand["Ollama LLM or deterministic fallback"]
    understand --> priority["Explainable priority and severity rules (0-100)"]
    priority --> db["PostgreSQL 17 via SQLAlchemy"]
    db --> resources["Nearby resources & availability"]
    resources --> ranking["Multi-factor ranking (40/30/30)"]
    ranking --> routing["Amazon Location Routes / OSRM fallback"]
    routing --> ui["Role-based operational UI"]
    api --> mapservice["Amazon Location Map Tile Proxy"]
    mapservice --> ui
    understand --> guidance["Precautions and role guidance"]
    guidance --> ui
    ui --> human["Authorized responder verification"]
```

### Processing sequence

1. A citizen report or sensor event enters the API.
2. Pydantic validates coordinates, counts, event values, and required fields.
3. The AI service attempts structured extraction through Ollama. A deterministic parser is used if the model is unavailable, slow, or returns invalid JSON.
4. `PriorityService` produces a bounded 0–100 score, severity label, and contributing factors.
5. `IncidentService` persists the incident and related extraction, severity, resource associations, and response recommendation records.
6. Resource and routing services calculate nearby facilities, suitability, distance, ETA, route steps, and map coordinates.
7. The UI presents verified data separately from AI assessment and operational recommendations.

## Operational workflows

> 💡 *For complete sequence diagrams, state transition models, edge IoT buffering, and failure handling procedures, see the comprehensive **[End-to-End Operational Workflows Guide](emergency-intelligence-response-main/docs/WORKFLOW.md)**.*

### Citizen portal — `/#user`

- Submit an emergency description and coordinates.
- View system priority, severity, status, precautions, and nearby emergency resources.
- View map markers and route information when responder/incident coordinates are available.

### Hospital triage — `/#hospital`

- Review incident telemetry, casualty counts, injuries, and critical indicators.
- View trauma preparation, receiving-bay, ICU, blood-bank, and ambulance-staging recommendations.
- Inspect route information from the hospital node to the incident.

### Police operations — `/#police`

- Review corridor-security and traffic-management guidance.
- View perimeter, diversion, lane-clearance, and dispatch recommendations.
- Inspect route and incident context for CAD coordination.

### Fire and rescue — `/#fire`

- Review extrication, suppression, hazard-scan, battery-isolation, and equipment guidance.
- View tactical staging and route information.

### Admin/CAD supervision — `/#admin`

- View active-incident totals, critical-incident counts, resource readiness, and system telemetry.
- Review the multi-agency overview returned by `/api/v1/dashboard/overview`.

The UI includes fallback display data so that the interface can still be explored when the backend is offline. Backend persistence and live resource data require a running PostgreSQL-backed API.

## Technology stack

| Area | Current implementation | Status note |
|---|---|---|
| Language | Python 3.10+, JavaScript (ES6+), C++ (PlatformIO / Arduino), HTML5, CSS3 | Implemented |
| API | FastAPI, Uvicorn, Pydantic v2 | Implemented |
| Persistence | PostgreSQL 17, SQLAlchemy 2.x, psycopg | Implemented |
| Migrations | Alembic | Implemented |
| AI runtime | Ollama HTTP API; configurable model; deterministic fallback parser | Implemented in hybrid form |
| NLP | Prompt-based extraction plus keyword/regex fallback | Implemented |
| Maps | Amazon Location Service Vector Tiles, MapLibre styles, Leaflet 1.9.4, OpenStreetMap tiles | Implemented in backend & UI |
| Routing | Amazon Location Routes (`geo:CalculateRoute`), OSRM HTTP service, local Haversine/tortuosity fallback | Implemented |
| IoT transport & Firmware | ESP32 C++ firmware (MPU-6050, DHT22, MQ-2, FSR, Sound, SIM800L, NVS Flash Queue) & FastAPI HTTP telemetry | Implemented |
| PostGIS | Described in design documents but not used by current models or queries | Planned |
| Embeddings/RAG | No embedding model, vector store, or retrieval pipeline in the current source tree | Planned |
| Frontend framework | Vanilla JavaScript; no React build is present in the current project | Implemented |

## GenAI, NLP, transformer, and geospatial roles

This project combines language technology with deterministic operational logic. The responsibilities are intentionally separated so that generated text does not decide dispatch priority or invent geographic facts.

| Concept | Responsibility in RESQ.AI | Repository status |
|---|---|---|
| NLP | Extract emergency type, casualty counts, injuries, critical indicators, and location hints from free text | Implemented through Ollama prompts and a regex/keyword fallback |
| Transformers | The external Ollama model is expected to be a transformer-based LLM runtime | Runtime integration exists; model weights are not stored in this repository |
| LLM | Generate structured extraction when Ollama responds within the configured timeout | Implemented through `/api/chat`; default is `qwen3:4b` |
| GenAI | Produce non-diagnostic precautions and role-specific operational guidance | Implemented through `AIService`; some guidance is deterministic templates |
| Prompt engineering | Strict JSON extraction instructions and bounded operational prompts | Implemented inline in `ai_service.py` |
| Qwen2.5-3B-Instruct | Referenced by the checked-in fine-tuning diagram as a target/base-model concept | Planned/documentary only; it is not the configured runtime model |
| BGE-M3 | Intended future semantic embedding model for retrieval | Not implemented; no BGE-M3 dependency or model is present |
| Embeddings | Would represent reports, procedures, and resources for semantic retrieval | Planned |
| RAG | Would ground responses in approved emergency procedures and verified operational documents | Planned; no vector store or retrieval code is present |
| ML/rules | Deterministic priority, severity, threshold, ranking, and routing fallback logic | Implemented as Python services; no separate trained ML model is present |
| Geospatial intelligence | Coordinates, Haversine distance, road-distance estimates, resource ranking, and route geometry | Implemented without PostGIS geometry queries |
| PostGIS | Intended spatial database layer for indexed geographic queries | Planned; current schema stores scalar latitude/longitude values |
| Database | Persist verified incident, resource, telemetry, assessment, and recommendation records | Implemented with PostgreSQL, SQLAlchemy, and Alembic |
| Response Copilot | Current role-specific response endpoint and dashboard guidance | Partially implemented; a conversational, retrieval-grounded copilot is planned |

The checked-in `RESQ_AI Fine Tuning Pipeline.drawio` describes a future fine-tuning and retrieval direction. It is design documentation, not evidence that fine-tuning, BGE-M3, embeddings, or RAG have already been executed.

## Repository structure

```text
.
├── emergency-intelligence-response-main/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/routes/          # Health, incidents, resources, routes, AI, IoT, dashboard
│   │   │   ├── core/                # Settings, logging, exception handling
│   │   │   ├── db/                  # Session and seed data
│   │   │   ├── models/              # SQLAlchemy persistence models
│   │   │   ├── schemas/             # Pydantic API contracts
│   │   │   └── services/            # AI, incidents, priority, resources, routing, IoT
│   │   ├── alembic/                 # Database migration configuration and revision
│   │   ├── .env.example             # Backend configuration template
│   │   └── requirements.txt
│   ├── docs/
│   │   ├── API_CONTRACT.md
│   │   ├── ARCHITECTURE.md
│   │   └── DATABASE_SCHEMA.md
│   ├── testing/test_backend.py
│   ├── database/                    # Database documentation placeholder
│   ├── datasets/                    # Dataset documentation placeholder
│   ├── genai/                       # GenAI documentation placeholder
│   ├── iot/                         # IoT documentation placeholder
│   ├── ml/                          # ML documentation placeholder
│   └── README.md                    # Backend-oriented project notes
├── resq.ai_emergency_response_platform/
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── server.py                    # Serves UI and mounts the canonical FastAPI app
│   └── *_operations/                # Role-specific design/code artifacts
├── RESQ_AI Fine Tuning Pipeline.drawio
├── RESQ_AI Whole_Module.pdf
└── Whole module.pdf
```

The repository does not currently contain valid screenshot assets for a README gallery. The checked-in `screen.png` files are 28-byte error placeholders rather than PNG images, so this README intentionally does not reference them as screenshots.

## Prerequisites

- Python 3.10 or newer.
- PostgreSQL compatible with the configured SQLAlchemy connection string. The project notes target PostgreSQL 14+ and commonly refer to PostgreSQL 17.
- `pip` and a virtual-environment module.
- Optional: [Ollama](https://ollama.com/) for local LLM extraction and generation. The backend remains usable through its deterministic fallback when Ollama is unavailable.
- Internet access is useful for live OSRM routes and browser-loaded Leaflet/OpenStreetMap assets. The backend has a local routing fallback, but external map assets still depend on browser connectivity.

## Local setup

From the repository root:

```bash
cd emergency-intelligence-response-main/backend
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create the backend environment file:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# macOS/Linux
cp .env.example .env
```

Edit `.env` before starting the service. The file is intentionally ignored by Git and must never be committed with real credentials.

## Running the platform

### Option A — unified UI and API server

This is the simplest local demonstration path. Keep the Python virtual environment activated:

```bash
cd ../../resq.ai_emergency_response_platform
python server.py
```

The wrapper imports the canonical backend from the sibling `emergency-intelligence-response-main/backend` directory, serves `index.html`, mounts the static UI, and listens on port `8000`.

Open:

- UI: <http://localhost:8000/#user>
- Hospital: <http://localhost:8000/#hospital>
- Police: <http://localhost:8000/#police>
- Fire: <http://localhost:8000/#fire>
- Admin/CAD: <http://localhost:8000/#admin>
- Swagger: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

### Option B — backend only

```bash
cd ../emergency-intelligence-response-main/backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Option C — static UI with a separate backend

Start the backend on port `8000`, then in another terminal:

```bash
cd resq.ai_emergency_response_platform
python -m http.server 5173
```

Open <http://localhost:5173/#user>. The configured CORS origins include `localhost:5173` and `127.0.0.1:5173`.

## Configuration

The backend reads `emergency-intelligence-response-main/backend/.env` through `pydantic-settings`.

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENV` | `development` | Runtime environment label |
| `APP_HOST` | `127.0.0.1` | Application host setting |
| `APP_PORT` | `8000` | Application port setting |
| `API_V1_STR` | `/api/v1` | Canonical API prefix |
| `PROJECT_NAME` | `RESQ.AI Emergency Intelligence & Response` | FastAPI project title |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/resq_ai` | PostgreSQL connection string |
| `CORS_ORIGINS` | localhost origins | Comma-separated allowed browser origins |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen3:4b` | Ollama model tag used by the current runtime |
| `DEFAULT_ROUTING_SPEED_KMH` | `40.0` | Local routing fallback speed |
| `PRIORITY_CRITICAL_THRESHOLD` | `75` | Minimum score for `CRITICAL` |
| `PRIORITY_HIGH_THRESHOLD` | `50` | Minimum score for `HIGH` |
| `PRIORITY_MODERATE_THRESHOLD` | `25` | Minimum score for `MODERATE` |

Priority bands are:

| Score | Severity |
|---:|---|
| 0–24 | `LOW` |
| 25–49 | `MODERATE` |
| 50–74 | `HIGH` |
| 75–100 | `CRITICAL` |

## Database and seed data

The current migration creates nine PostgreSQL tables:

1. `users`
2. `emergency_reports`
3. `ai_extractions`
4. `severity_assessments`
5. `emergency_resources`
6. `resource_availability`
7. `incident_resources`
8. `sensor_readings`
9. `response_recommendations`

Create the database using your local PostgreSQL administration tooling, for example:

```bash
createdb -U postgres resq_ai
```

Then apply the migration and seed the demonstration data:

```bash
cd emergency-intelligence-response-main/backend
python -m alembic upgrade head
python -m app.db.seed_demo_data
```

The seed script is idempotent for the existing resource and incident identifiers used by the demo. It creates verified resource records, availability information, responder nodes, users, and baseline incidents.

### Current geospatial database status

The documentation includes a future PostGIS design, but the current SQLAlchemy models store ordinary latitude and longitude columns. Nearby-resource calculations currently use Haversine distance plus a road-distance multiplier; no PostGIS extension, geometry column, spatial index, or `ST_*` query is present in the codebase. PostGIS is therefore a planned enhancement, not a completed dependency.

## API reference

Canonical base URL: `http://127.0.0.1:8000/api/v1`

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Database and service health |
| `POST` | `/incidents` | Create an incident and run extraction, scoring, persistence, and recommendations |
| `GET` | `/incidents` | List active and recent incidents |
| `GET` | `/incidents/{incident_id}` | Fetch one incident with analysis and recommendations |
| `PATCH` | `/incidents/{incident_id}` | Update status, casualty counts, or description |
| `GET` | `/resources` | List verified resources near the demonstration operating center |
| `GET` | `/resources/nearby` | Find nearby resources by coordinates, type, and radius |
| `POST` | `/resources/rank` | Rank resources by distance, availability, and suitability |
| `GET` | `/routes` | Calculate a route using OSRM or the local fallback |
| `POST` | `/routes` | POST variant of route calculation |
| `POST` | `/ai/extract` | Extract structured incident fields from free text |
| `POST` | `/ai/precautions` | Generate non-diagnostic public-safety precautions |
| `POST` | `/ai/response` | Generate hospital, police, or fire operational guidance |
| `POST` | `/iot/events` | Ingest ESP32-style telemetry and trigger incidents at thresholds |
| `GET` | `/dashboard/overview` | Return CAD counters, readiness, incidents, resources, and telemetry |
| `GET` | `/dashboard/incidents` | Return dashboard incident data |
| `GET` | `/dashboard/resources` | Return dashboard resource data |

The backend also registers compatibility routes under `/api/...` and selected root paths. New clients should use `/api/v1/...`.

### Incident creation fields

`POST /api/v1/incidents` accepts:

- `description` — required free-text report, minimum five characters.
- `latitude`, `longitude` — required geographic coordinates.
- `location` or `location_name` — optional human-readable location.
- `affected_people`, `injuries` — non-negative counts.
- `critical_indicators` — optional list of indicators.
- `emergency_type` — optional explicit type; otherwise inferred.
- `user_priority` — optional 0–100 user-provided priority.
- `source` — defaults to `USER`; IoT-created incidents use `IOT`.

### IoT thresholds

The current ingestion service records every validated reading and creates an incident when any of these conditions are met:

- Accident: `impact >= 5.0 G` or `event_type == ACCIDENT`.
- Fire: `smoke_level >= 1500 ppm`, `temperature >= 60°C`, or `event_type == FIRE`.
- Flood: `water_level >= 50 cm` or `event_type == FLOOD`.

These are demonstration thresholds and should be calibrated against real sensor hardware before operational use.

## Example requests

### Create an incident

```bash
curl -X POST http://127.0.0.1:8000/api/v1/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Major accident near the highway. Three people are injured and one person is unconscious.",
    "latitude": 12.9352,
    "longitude": 77.6944,
    "location": "Outer Ring Road, Bengaluru",
    "affected_people": 3,
    "injuries": 3,
    "source": "USER"
  }'
```

### Query nearby resources

```bash
curl "http://127.0.0.1:8000/api/v1/resources/nearby?latitude=12.9352&longitude=77.6944&radius=15"
```

### Submit ESP32-style telemetry

```bash
curl -X POST http://127.0.0.1:8000/api/v1/iot/events \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ESP32_CRASH_NODE_01",
    "event_type": "ACCIDENT",
    "temperature": 32.5,
    "smoke_level": 400.0,
    "impact": 8.7,
    "latitude": 12.9352,
    "longitude": 77.6944
  }'
```

### Calculate a route

```bash
curl "http://127.0.0.1:8000/api/v1/routes?origin_lat=12.9550&origin_lng=77.6500&destination_lat=12.9352&destination_lng=77.6944&origin_name=City%20Care%20Hospital&destination_name=Accident%20Site"
```

## Roadmap and implementation status

The following status is derived from the current source tree, tests, configuration, and checked-in design documents.

| Stage | Status | Evidence and scope |
|---|---|---|
| Hardware / ESP32 | 🟡 In progress | Backend schema, HTTP ingestion, sensor bounds, and threshold handling exist; ESP32 firmware and hardware integration are not included. |
| Backend / API | ✅ Completed for current scope | FastAPI application, route modules, validation schemas, exception handling, CORS, and automated endpoint tests are present. |
| Database | ✅ Completed | PostgreSQL persistence, SQLAlchemy models, Alembic migration, and seed data are present; PostGIS geometry support is not implemented. |
| Real-Time Emergency Pipeline | 🟡 In progress | Synchronous report/telemetry → extraction → scoring → persistence flow exists; no message broker, WebSocket, or background event pipeline is present. |
| GenAI | ✅ Completed | Ollama integration, strict JSON extraction, fallback NLP, precautions, and role guidance exist; fine-tuned model artifacts are absent. |
| RAG | ⚪ Planned | No embeddings, BGE-M3 integration, vector database, document chunking, or retrieval service is present. |
| PostGIS / Resources / Routing | ✅ Completed | Resource discovery, ranking, Haversine calculations, OSRM routing, and local fallback exist; PostGIS queries and spatial indexes are planned. |
| Response Copilot | ✅ Completed | Role-specific `/ai/response` guidance and dashboard cards exist; conversational, retrieval-grounded copilot behavior is planned. |
| Dashboard | ✅ Completed | Five role views, Leaflet maps, API synchronization, fallback UI data, and CAD overview are present; some actions are UI alerts rather than persisted workflows. |
| End-to-End Demo | ✅ Completed | Unified server and backend tests support a local demo; there is no automated browser E2E suite or production deployment configuration. |
| Testing / Documentation | 🟡 In progress | Nine backend tests pass and architecture/API/database documents exist; CI, coverage reporting, valid screenshots, and full operational documentation are still being developed. |

### Planned milestones

1. Add and validate real ESP32 firmware, device authentication, and reliable telemetry delivery.
2. Add PostGIS geometry columns, spatial indexes, and database-side nearby-resource queries.
3. Add approved emergency-procedure documents, BGE-M3 embeddings, a vector store, and a grounded RAG service.
4. Separate model prompts and configuration from application code and evaluate model outputs against a labeled dataset.
5. Add authentication, role-based authorization, responder identity, audit records, and secure secret management.
6. Add event streaming or a broker for live telemetry, notifications, and dashboard updates.
7. Add automated browser E2E tests, coverage, CI, observability, and deployment documentation.

## Academic relevance

RESQ.AI is primarily relevant to **SDG 11 — Sustainable Cities and Communities** because it explores technology-assisted emergency coordination, situational awareness, resource discovery, and resilient response workflows for urban environments.

Supporting relevance includes:

- **SDG 3 — Good Health and Well-Being:** helps organize incident information and hospital/triage preparation guidance. It does not diagnose patients or replace clinicians.
- **SDG 9 — Industry, Innovation and Infrastructure:** combines an API, database, local AI inference, geospatial services, and IoT-style telemetry in one applied system.
- **SDG 13 — Climate Action:** the flood and sensor-event pathway can support climate-related hazard awareness and coordination. The repository does not claim climate prediction or emissions reduction.

The academic contribution is therefore an applied prototype for intelligent emergency response support, resilient communities, and technology-assisted coordination—not an autonomous dispatch authority or a validated public-safety deployment.

## Team contributions

The current repository does not contain an authoritative team roster or a verified responsibility allocation. To avoid inventing names or contributions, this README does not assign individual ownership. The repository itself contains work areas for:

- Full-stack API/UI integration.
- GenAI and NLP decision support.
- Dataset and ML experimentation.
- Hardware and IoT telemetry.
- Database, GIS resources, and routing.
- Testing and documentation.

These areas describe repository structure, not confirmed individual authorship. Add the official team names and approved responsibilities here when that information is committed to the project documentation.

## Testing and validation

Run the backend test suites from the backend project root:

```bash
cd emergency-intelligence-response-main

# Run core backend and API tests
python -m pytest testing/test_backend.py -v

# Run Amazon Location Service integration tests
python -m pytest testing/test_amazon_location.py -v
```

The checked-in test suites cover:

- Health and database connectivity.
- Incident creation and persistence of AI extraction and severity assessment.
- Incident listing and retrieval.
- Nearby-resource discovery and ETA calculation.
- Multi-factor resource ranking (proximity, capacity, type match).
- Amazon Location Service routing and OSRM/local-fallback calculation.
- Map tile and style proxy endpoint response handling.
- Non-diagnostic precautions and hospital/police/fire role intelligence.
- IoT event ingestion and threshold-triggered incident creation.

Additional syntax checks used during repository validation:

```bash
cd emergency-intelligence-response-main
python -m compileall -q backend

cd ../resq.ai_emergency_response_platform
python -m py_compile server.py
node --check app.js
```

The repository currently has no CI workflow, coverage threshold, automated browser test, or deployment smoke test.

## Limitations and planned work

- **No authentication or authorization:** the API does not currently enforce user identity or responder roles.
- **No production dispatch integration:** UI acknowledgement and dispatch-style actions are not a replacement for official CAD or emergency-service dispatch systems.
- **Hardware calibration & deployment:** ESP32 C++ firmware with non-volatile flash buffering is provided in `emergency-intelligence-response-main/iot/`; field installations require analog ADC calibration against real smoke/gas levels.
- **No RAG or embeddings:** responses are generated from prompt logic, deterministic templates, and the local fallback parser; they are not grounded against an indexed policy corpus.
- **No fine-tuned model:** the checked-in drawio diagram describes a Qwen2.5-3B-Instruct/LoRA-style direction, but no training script, weights, evaluation set, or fine-tuning run is present.
- **No PostGIS implementation:** current geospatial logic uses scalar coordinates, Haversine distance, multipliers, and Amazon Location / OSRM HTTP results.
- **External routing and map assets:** Amazon Location Service, OSRM, and Leaflet CDN assets require network access; routing has a multi-tier fallback (AWS → OSRM → Haversine), but offline vector tiles require local caching.
- **Demonstration thresholds and seed data:** sensor thresholds, locations, capabilities, and response templates require operational validation before real use.
- **Limited persistence for UI actions:** some UI interactions show alerts or update local state rather than writing a responder audit event to the database.

## Safety and data considerations

- Do not use generated precautions or recommendations as medical diagnosis, legal advice, or an autonomous dispatch decision.
- Verify incident coordinates, casualty counts, sensor readings, resource availability, and route conditions with authorized personnel.
- Keep `.env` files, database credentials, Ollama access details, AWS access keys, and any personally identifiable information out of commits.
- Review and calibrate all sensor thresholds and operational templates with qualified emergency-response stakeholders.
- Treat public OSRM/OpenStreetMap services as development/demo dependencies and review their usage policies before deployment.

## Additional documentation

- [Comprehensive architecture and engineering design](emergency-intelligence-response-main/docs/ARCHITECTURE.md)
- [End-to-end operational workflows](emergency-intelligence-response-main/docs/WORKFLOW.md)
- [API contract](emergency-intelligence-response-main/docs/API_CONTRACT.md)
- [Database schema](emergency-intelligence-response-main/docs/DATABASE_SCHEMA.md)
- [ESP32 IoT firmware guide](emergency-intelligence-response-main/iot/README.md)
- [Backend project notes](emergency-intelligence-response-main/README.md)
- [Backend environment template](emergency-intelligence-response-main/backend/.env.example)
- [Backend dependencies](emergency-intelligence-response-main/backend/requirements.txt)
- [Backend core tests](emergency-intelligence-response-main/testing/test_backend.py)
- [Amazon Location tests](emergency-intelligence-response-main/testing/test_amazon_location.py)
- [Operational UI notes](resq.ai_emergency_response_platform/README.md)
- [Fine-tuning pipeline design artifact](RESQ_AI%20Fine%20Tuning%20Pipeline.drawio)

## License

No license file is currently present in the repository. Add an approved license before redistributing the project.
