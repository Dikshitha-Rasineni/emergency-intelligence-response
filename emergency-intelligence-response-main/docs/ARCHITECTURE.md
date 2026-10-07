# RESQ.AI — Architecture & Operational Design

## System Purpose & Scope
**RESQ.AI** is a geospatial decision-support system designed to ingest emergency reports from citizens and IoT sensor nodes, assess severity, calculate priority, identify verified nearby emergency resources, compute GIS routing metrics, and generate tailored, non-diagnostic response recommendations for authorized human responders across 5 operational roles.

---

## High-Level Data Flow

```
                      RESQ.AI Pipeline
                      
  Citizen Input (Web)               ESP32 Sensor Telemetry
          │                                   │
          └─────────────────┬─────────────────┘
                            ▼
               Data Validation & Normalization
                            ▼
           AI Incident Understanding & Extraction
              (Ollama Qwen/Llama + Fallback)
                            ▼
               Structured Incident Record
                            ▼
          Deterministic Priority & Severity Engine
              (0–100 Explainable Scoring)
                            ▼
            PostgreSQL Database Persistence
               (9-Table Relational Schema)
                            ▼
        Geospatial Resource Discovery & Spatial Matrix
                            ▼
                 Multi-Factor Resource Ranking
          (Proximity, Availability, Capacity, Match)
                            ▼
                   GIS Routing & ETA Engine
              (Road-Tortuosity & Real Coordinates)
                            ▼
               Response Recommendations & Precaution
               (Clinical & Tactical Action Guides)
                            ▼
              Role-Specific CAD Dashboards
        ┌───────────┬───────────┬───────────┬───────────┐
        ▼           ▼           ▼           ▼           ▼
     Citizen     Hospital      Police      Fire       Admin
     Portal       Triage     Operations   Rescue    Supervision
        │           │           │           │           │
        └───────────┴───────────┴───────────┴───────────┘
                            ▼
             Human Verification & Action
```

---

## Architectural Layers

### 1. Ingestion & Validation Layer
- Pydantic models validate all coordinates, casualty counts, and sensor bounds.
- Dual-alias support (`location` / `location_name`, `system_priority` / `priority_score`, `type` / `resource_type`) prevents frontend contract breakage.
- Telemetry threshold filters in IoT ingestion prevent sensor noise from creating false alarms.

### 2. Emergency Understanding (Hybrid GenAI)
- Queries local Ollama model (`qwen3:4b` or `llama3:instruct`) with strict JSON schema instructions.
- If Ollama is unavailable or times out (>3.0s), an internal high-precision regex/keyword parser extracts emergency type, casualty numbers, and critical indicators without dropping requests.
- Strict non-diagnostic disclaimer is appended to all guidance.

### 3. Priority & Severity Engine
- Fully deterministic and explainable:
  - Base score: 25
  - Unconscious / cardiac / life-threat: +35
  - Active fire / trapped personnel / smoke: +30
  - Corridor collision: +20
  - Injury multiplier: up to +30
  - Affected people scaling: up to +15
  - Specific critical indicators (e.g. gas cylinders): +10
- Scores strictly map to:
  - `0–24`: LOW
  - `25–49`: MODERATE
  - `50–74`: HIGH
  - `75–100`: CRITICAL

### 4. Database Layer (PostgreSQL 17)
- 9 relational tables with foreign keys and cascade rules.
- Managed by Alembic migrations (`alembic/versions/256a96bd5612_initial_9_table_schema.py`).
- Pre-seeded with verified Bangalore public safety stations and baseline incidents.

### 5. Geospatial Discovery & Multi-Factor Ranking
- Uses great-circle distance queries across all registered resources.
- Ranking algorithm balances:
  - Road Proximity (40%)
  - Live Capacity / Available Units (30%)
  - Incident Type Match (30%)

### 6. Routing & Navigation Engine
- Completely separated from the LLM to prevent hallucinated travel times.
- Calculates realistic road network distances using an urban tortuosity multiplier (~1.25x-1.35x).
- Uses standard emergency vehicle transit speeds (40 km/h) plus dispatch delay.
- Computes turn-by-turn waypoint coordinates for map visualization in Leaflet.

### 7. Human Decision-Support Interface
- Strict separation of verified facts from AI suggestions.
- Interactive responder acknowledgement workflow logging time and officer ID to the CAD ledger.
