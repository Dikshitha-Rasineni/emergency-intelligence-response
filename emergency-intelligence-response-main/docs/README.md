# RESQ.AI — Documentation Hub

Welcome to the technical and operational documentation directory for **RESQ.AI**.

---

## Documentation Index

| Document | Description |
|---|---|
| [System Architecture (`ARCHITECTURE.md`)](file:///c:/Users/moury/Coding/Projects/GENAI-Project/emergency-intelligence-response-main/docs/ARCHITECTURE.md) | Comprehensive engineering architecture, multi-tier system topology, component responsibilities, mathematical scoring models, and edge hardware specifications. |
| [Operational Workflows (`WORKFLOW.md`)](file:///c:/Users/moury/Coding/Projects/GENAI-Project/emergency-intelligence-response-main/docs/WORKFLOW.md) | End-to-end incident lifecycle, IoT sensor event ingestion, hybrid AI processing flows, multi-factor ranking, and edge-to-cloud failover matrices. |
| [API Contract (`API_CONTRACT.md`)](file:///c:/Users/moury/Coding/Projects/GENAI-Project/emergency-intelligence-response-main/docs/API_CONTRACT.md) | Complete REST API endpoint reference, Pydantic schemas, request/response JSON contracts, and query parameters. |
| [Database Schema (`DATABASE_SCHEMA.md`)](file:///c:/Users/moury/Coding/Projects/GENAI-Project/emergency-intelligence-response-main/docs/DATABASE_SCHEMA.md) | Detailed schema specification for PostgreSQL 17, Alembic migration history, table definitions, foreign keys, and index configurations. |

---

## Core System Overview

```
                                  RESQ.AI
  Edge Telemetry & Citizen Intake ──► Hybrid Decision Support ──► Multi-Agency CAD
  (ESP32 + Pydantic Validation)        (Ollama + Deterministic)    (5 Role Dashboards)
```

1. **Intake & Edge**: ESP32 sensor hardware with multi-sensor monitoring (MPU6050, DHT22, MQ-2, FSR, Sound) and citizen browser geolocation intake.
2. **Intelligence**: Hybrid LLM extraction with deterministic fallback, 0–100 explainable priority scoring, and non-diagnostic safety guardrails.
3. **Geospatial & Navigation**: Amazon Location Service route calculation and backend vector tile proxying with automatic fallback to OSRM and Haversine tortuosity.
4. **Operations**: Real-time role-based dashboards for Citizen, Hospital Trauma Triage, Police Patrol CAD, Fire & Hazmat Rescue, and Dispatch Supervisors.
