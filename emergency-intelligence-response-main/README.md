# RESQ.AI — Emergency Intelligence & Decision-Support System

RESQ.AI transforms unstructured emergency signals from citizens and IoT sensor stations into actionable, role-specific operational intelligence for hospitals, police forces, fire & rescue brigades, and CAD dispatch supervisors.

> **Operational Safety Principle:** RESQ.AI is a **DECISION-SUPPORT SYSTEM**. The AI does not autonomously dispatch emergency services. All recommendations and priority scores are presented as decision-support guidance for authorized human responders.

---

## Architecture Overview

```
                      RESQ.AI Architecture
                      
 Citizen Web Portal                ESP32 IoT Gateway
         │                                 │
         └───────────────┬─────────────────┘
                         ▼
             FastAPI Canonical REST API
             (/api/v1/... + /api/...)
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
    Validation Layer        AI Extraction & Reasoning
             │              (Ollama Qwen/Llama + Fallback)
             ▼                       │
    Priority & Severity              │
      Scoring Engine                 │
             │                       │
             ▼                       ▼
     PostgreSQL 17 DB        Response Recommendations
   (Alembic 9-Table Schema)    (Non-Diagnostic Guidance)
             │                       │
             ▼                       ▼
   Geospatial Discovery       GIS Routing & ETA
   & Multi-Factor Ranking    (Road-Tortuosity Matrix)
             │                       │
             └───────────┬───────────┘
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

## Running the Platform

### 1. Requirements
- Python 3.10+
- PostgreSQL 17 (or 14+) with database `resq_ai`
- Ollama (optional, local LLM inference)

### 2. Environment Setup
```bash
cd emergency-intelligence-response-main/backend
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

## Automated Test Suite

Run comprehensive automated tests verifying all APIs and database persistence:
```bash
cd emergency-intelligence-response-main
python -m pytest testing/test_backend.py -v
```

---

## API Summary (Canonical `/api/v1/...`)

- `GET  /api/v1/health` — Database and system connectivity check
- `POST /api/v1/incidents` — Create incident with AI extraction, priority scoring, and DB persistence
- `GET  /api/v1/incidents` — List active incidents
- `GET  /api/v1/incidents/{id}` — Get single incident telemetry
- `PATCH /api/v1/incidents/{id}` — Update incident status (e.g. ACKNOWLEDGED)
- `GET  /api/v1/resources/nearby` — Discover verified emergency facilities within radius
- `POST /api/v1/resources/rank` — Multi-factor ranking (proximity, capacity, emergency match)
- `GET  /api/v1/routes` — Road routing distance, ETA, and GIS coordinates
- `POST /api/v1/ai/extract` — Structured extraction from text
- `POST /api/v1/ai/precautions` — Non-diagnostic citizen safety guidelines
- `POST /api/v1/ai/response` — Role-specific staging guidelines (Hospital, Police, Fire)
- `POST /api/v1/iot/events` — Ingest ESP32 telemetry with automated incident triggering
- `GET  /api/v1/dashboard/overview` — CAD overview with live sector counters
