# RESQ.AI — Emergency Intelligence & Decision-Support System

RESQ.AI transforms unstructured emergency signals from citizens and IoT sensor stations into actionable, role-specific operational intelligence for hospitals, police forces, fire & rescue brigades, and CAD dispatch supervisors.

> **Operational Safety Principle:** RESQ.AI is a **DECISION-SUPPORT SYSTEM**. The AI does not autonomously dispatch emergency services. All recommendations and priority scores are presented as decision-support guidance for authorized human responders.

---

## Technical Documentation

- **[System Architecture (`docs/ARCHITECTURE.md`)](file:///c:/Users/moury/Coding/Projects/GENAI-Project/emergency-intelligence-response-main/docs/ARCHITECTURE.md)**: Deep dive into the multi-layer system architecture, Amazon Location Service integration, and mathematical scoring models.
- **[Operational Workflows (`docs/WORKFLOW.md`)](file:///c:/Users/moury/Coding/Projects/GENAI-Project/emergency-intelligence-response-main/docs/WORKFLOW.md)**: Sequence diagrams and step-by-step procedures for citizen reporting, IoT event synthesis, failover resilience, and CAD verification.
- **[API Contract (`docs/API_CONTRACT.md`)](file:///c:/Users/moury/Coding/Projects/GENAI-Project/emergency-intelligence-response-main/docs/API_CONTRACT.md)**: Complete OpenAPI specification covering all canonical `/api/v1` endpoints and request/response payloads.
- **[Database Schema (`docs/DATABASE_SCHEMA.md`)](file:///c:/Users/moury/Coding/Projects/GENAI-Project/emergency-intelligence-response-main/docs/DATABASE_SCHEMA.md)**: PostgreSQL 17 relational schema, foreign key relations, and Alembic migration details.

---

## Architecture Overview

```
                      RESQ.AI Architecture
                      
 Citizen Web Portal                ESP32 IoT Edge Node
         │                         (MPU6050, DHT22, MQ2, FSR, SIM800L)
         │                                   │
         └─────────────────┬─────────────────┘
                           ▼
               FastAPI Canonical REST API
             (/api/v1/... + Map Tile Proxy)
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
  Validation Layer  AI Extraction & NLP  Amazon Location Service
         │          (Ollama + Fallback)  (Routes + Vector Maps)
         ▼                 │                 │
Priority & Severity        │                 │
  Scoring Engine           │                 │
         │                 │                 │
         ▼                 ▼                 ▼
 PostgreSQL 17 DB   Response Directives  GIS Routing & ETA
(9-Table Relational (Clinical/Tactical   (Amazon Location
      Schema)           Safety)            + OSRM Fallback)
         │                 │                 │
         └─────────────────┼─────────────────┘
                           ▼
          Role-Specific Operational Dashboards
   ┌─────────────┬─────────────┬─────────────┬─────────────┐
   ▼             ▼             ▼             ▼             ▼
Citizen      Hospital       Police         Fire        Admin CAD
Portal        Triage      Operations     & Rescue     Supervision
```

---

## 9-Table Database Schema

Managed via Alembic in PostgreSQL:
1. `users`: Role-based system users (`citizen`, `hospital`, `police`, `fire`, `admin`).
2. `emergency_reports`: Canonical incident table with coordinates, descriptions, and statuses.
3. `ai_extractions`: Extracted emergency type, casualty counts, critical indicators.
4. `severity_assessments`: Deterministic priority score (0–100), severity level, and contributing factors.
5. `emergency_resources`: Hospital trauma centers, ALS/BLS ambulances, police stations, fire stations.
6. `resource_availability`: Live bed counts, operational tenders, patrol units, and availability status.
7. `incident_resources`: Proximity associations, suitability ranking, and distance metrics.
8. `sensor_readings`: ESP32 telemetry (impact Gs, smoke PPM, water level, temperature).
9. `response_recommendations`: Role-specific checklists, staging precautions, and missing info flags.

---

## IoT Edge Firmware (`iot/`)

The repository includes complete production C++ firmware for the **ESP32 DevKit V1**:
- **Sensor Suite**: MPU-6050 (impact/crash acceleration), DHT22 (ambient fire temperature), MQ-2 (smoke & combustible gases), FSR (impact force), Sound (blast detection), SIM800L (GSM/GPRS fallback).
- **Edge Intelligence**: Multi-sample debounce filters, threshold-based incident generation, and routine heartbeats.
- **Fail-Safe Flash Buffer**: Buffers up to 8 emergency events in non-volatile flash memory (`Preferences` / NVS) with priority eviction when offline. Automatically drains once WiFi is restored.
- **Build & Flash**:
  ```bash
  cd iot
  # Copy secrets template and set WiFi credentials
  cp include/secrets.example.h include/secrets.h
  # Build and flash using PlatformIO
  pio run --target upload
  ```

---

## Amazon Location Service Integration

The platform leverages **Amazon Location Service** for high-precision routing and map rendering:
- **Routes (`geo:CalculateRoute`)**: Computes real-world road network distance, travel duration, and route geometry using the `resq-ai-routing` calculator.
- **Map Vector Tiles & Styles**: Proxied through FastAPI (`/api/v1/maps/style.json`, `/tiles/{z}/{x}/{y}`, `/glyphs/...`, `/sprites/...`) using backend IAM credentials, bypassing browser API key constraints.
- **Graceful Multi-Tier Fallback**: Automatically degrades to OSRM and local Haversine tortuosity calculations if AWS credentials or network connectivity are unavailable.

---

## Running the Platform

### 1. Requirements
- Python 3.10+
- PostgreSQL 17 (or 14+) with database `resq_ai`
- Ollama (optional, for local LLM inference)
- AWS Credentials configured with Amazon Location permissions (optional, for live AWS maps & routing)

### 2. Environment Setup
```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
```

### 3. Run Migrations & Seed Data
```bash
# Apply Alembic schema migrations
python -m alembic upgrade head

# Seed verified emergency resources, responder nodes, and baseline incidents
python -m app.db.seed_demo_data
```

### 4. Start Server
```bash
# Option A: Start the unified platform server (API + Frontend UI on port 8000)
cd ../../resq.ai_emergency_response_platform
python server.py

# Option B: Run FastAPI backend directly from backend folder
cd ../emergency-intelligence-response-main/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- Platform UI: `http://localhost:8000/#user`
- Swagger OpenAPI Docs: `http://localhost:8000/docs`
- ReDoc Docs: `http://localhost:8000/redoc`

---

## Automated Test Suites

Run the full automated test suite verifying backend logic, persistence, and Amazon Location Service:
```bash
cd emergency-intelligence-response-main

# Run backend core tests
python -m pytest testing/test_backend.py -v

# Run Amazon Location Service integration tests
python -m pytest testing/test_amazon_location.py -v
```

---

## API Summary (Canonical `/api/v1/...`)

- `GET  /api/v1/health` — Database, decision support, and routing connectivity check
- `POST /api/v1/incidents` — Create incident with AI extraction, priority scoring, and DB persistence
- `GET  /api/v1/incidents` — List active incidents
- `GET  /api/v1/incidents/{id}` — Get single incident telemetry
- `PATCH /api/v1/incidents/{id}` — Update incident status (e.g., ACKNOWLEDGED)
- `GET  /api/v1/resources/nearby` — Discover verified emergency facilities within radius
- `POST /api/v1/resources/rank` — Multi-factor ranking (proximity, capacity, emergency match)
- `GET  /api/v1/routes` — Road routing distance, ETA, and GIS coordinates (Amazon Location / OSRM)
- `GET  /api/v1/maps/style.json` — MapLibre style descriptor proxy for Amazon Location
- `GET  /api/v1/maps/tiles/{z}/{x}/{y}` — Vector tile proxy for Amazon Location maps
- `POST /api/v1/ai/extract` — Structured extraction from text
- `POST /api/v1/ai/precautions` — Non-diagnostic citizen safety guidelines
- `POST /api/v1/ai/response` — Role-specific staging guidelines (Hospital, Police, Fire)
- `POST /api/v1/iot/events` — Ingest ESP32 telemetry with automated incident triggering
- `GET  /api/v1/dashboard/overview` — CAD overview with live sector counters
