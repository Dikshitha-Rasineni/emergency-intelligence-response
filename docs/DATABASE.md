# Database

PostgreSQL 16 + PostGIS 3.4 (any PostgreSQL ≥14 with PostGIS 3 works). Migrations in `backend/alembic/versions` (head `d4f1a2b3c4d5`); upgrade and downgrade were both run during development.

| Table | Purpose |
|---|---|
| `emergency_reports` | Canonical incidents and merged reports (`merged_into_id`). Original text, language + confidence, preferred language, location source/verification/accuracy, category, status, `ai_status`, hashed tracking token. **`geom geography(Point)`** maintained by trigger, GiST index |
| `ai_extractions` | Every extraction (rule-based and LLM) with method, model, latency, validation notes, hazards, needs, uncertainties, English summary |
| `severity_assessments` | Every assessment: score, severity, evidence list with sources, uncertainties, version, assessed_by, override reason |
| `routing_decisions` | Per department: included, role, reasons, policy version, superseded flag (history kept) |
| `notifications` | One per (incident, department, channel); status, attempts, deadline, ack, escalation, full history |
| `incident_updates` | Status changes and notes; `public` flag controls citizen visibility |
| `incident_media` | Image metadata, private storage key, sha256, EXIF-GPS flag, duplicate link, status, validated analysis JSON, retention date |
| `emergency_resources` | Facilities (`verified`, `data_source` ADMIN/DEMO_SEED/OSM). **`geom`** + GiST index |
| `resource_availability` | Status reported by an authorised organisation user (`verified`), otherwise UNKNOWN |
| `incident_resources` | Nearest facilities per incident (straight-line km from PostGIS) |
| `sensor_readings` | All IoT readings; unique `event_id`; transport; raw ADC values |
| `iot_devices` | Registered devices, installed location, last seen, firmware |
| `users`, `organizations` | Accounts (PBKDF2 password hash), role, organisation, operated resource |
| `audit_events` | Who did what, when (no citizen free text or images) |
| `knowledge_documents`, `knowledge_chunks` | RAG corpus; chunks have a generated `tsvector` + GIN index |
| `response_recommendations` | Citizen guidance stored with the assessment (language, sources) |

Retention: `MEDIA_RETENTION_DAYS` sets `purge_after` on images; `POST /admin/media/purge` deletes expired files and rows. Citizen reports contain no names or phone numbers by design.
