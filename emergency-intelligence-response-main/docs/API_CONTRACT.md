# RESQ.AI — Official API Contract (v1.0.0)

**Base URL:** `http://127.0.0.1:8000/api/v1`  
*(Legacy aliases supported under `/api/...` and `/...`)*

---

## 1. System Health & Readiness

### `GET /api/v1/health`
Checks backend and database connectivity.

**Response `200 OK`:**
```json
{
  "status": "healthy",
  "service": "resq-ai-backend",
  "database": "connected",
  "decision_support": "operational",
  "routing_service": "gis-connected"
}
```

---

## 2. Emergency Incidents

### `POST /api/v1/incidents`
Submits an emergency incident. Triggers automated AI extraction, priority calculation, and initial resource ranking.

**Request Body:**
```json
{
  "description": "Major accident near highway. Three people injured and one person is unconscious.",
  "latitude": 12.9352,
  "longitude": 77.6944,
  "location": "Outer Ring Road, KM 14.2 Southbound, Bengaluru",
  "location_name": "Outer Ring Road, KM 14.2 Southbound, Bengaluru",
  "affected_people": 3,
  "injuries": 3,
  "critical_indicators": ["Unconscious casualty reported"],
  "emergency_type": "Major Road Accident",
  "source": "USER"
}
```

**Response `201 Created`:**
```json
{
  "incident_id": "INC-D4457C47",
  "id": "INC-D4457C47",
  "description": "Major accident near highway...",
  "latitude": 12.9352,
  "longitude": 77.6944,
  "location_name": "Outer Ring Road, KM 14.2 Southbound, Bengaluru",
  "location": "Outer Ring Road, KM 14.2 Southbound, Bengaluru",
  "affected_people": 3,
  "injuries": 3,
  "critical_indicators": ["Unconscious casualty reported"],
  "emergency_type": "Major Road Accident",
  "priority_score": 82,
  "system_priority": 82,
  "user_priority": 82,
  "severity": "CRITICAL",
  "status": "REPORTED",
  "source": "USER",
  "created_at": "2026-10-06T19:00:00Z",
  "updated_at": "2026-10-06T19:00:00Z",
  "precautions": ["..."],
  "recommendations": { "summary": "...", "recommendation": "..." }
}
```

### `GET /api/v1/incidents`
Lists all active and recent incidents.

**Response `200 OK`:** Array of incident objects.

### `GET /api/v1/incidents/{incident_id}`
Retrieves a specific incident by ID.

### `PATCH /api/v1/incidents/{incident_id}`
Updates incident status (`ACKNOWLEDGED`, `DISPATCHED`, `RESOLVED`) or casualty figures.

---

## 3. Geospatial Resource Discovery & Ranking

### `GET /api/v1/resources/nearby`
Finds verified emergency resources (hospitals, ambulances, police, fire) within radius.

**Query Parameters:**
- `latitude` (float, required)
- `longitude` (float, required)
- `type` (optional: `HOSPITAL`, `AMBULANCE`, `POLICE`, `FIRE`)
- `radius` (float, default `25.0` km)

**Response `200 OK`:**
```json
[
  {
    "id": "RES-H1",
    "resource_id": "RES-H1",
    "name": "City Care Hospital",
    "type": "HOSPITAL",
    "resource_type": "HOSPITAL",
    "latitude": 12.9550,
    "longitude": 77.6500,
    "distance_km": 2.4,
    "eta_min": 8,
    "availability": "Emergency Department Available",
    "capability": "Trauma Care Level-1 · 6 ICU Beds Ready",
    "contact": "+91 80 2520 1100"
  }
]
```

### `POST /api/v1/resources/rank`
Ranks nearby resources considering proximity, availability, capacity, and emergency match.

---

## 4. Routing & ETA Service

### `GET /api/v1/routes`
Calculates origin-to-destination road distance, realistic transit ETA, and GIS coordinate waypoints.

**Query Parameters:**
- `origin_lat`, `origin_lng`
- `destination_lat`, `destination_lng`
- `origin_name`, `destination_name`

**Response `200 OK`:**
```json
{
  "origin_name": "City Care Hospital",
  "destination_name": "Outer Ring Road Incident",
  "distance_km": 4.8,
  "eta_min": 8,
  "route_corridor": "Priority corridor via Arterial Main to Outer Ring Road",
  "steps": [
    { "instruction": "Depart City Care Hospital ramp...", "distance_km": 0.7, "duration_min": 1.2 }
  ],
  "coordinates": [[12.9550, 77.6500], [12.9480, 77.6650], [12.9352, 77.6944]],
  "routing_status": "GIS_CALCULATED"
}
```

---

## 5. AI Decision Support & Copilot

### `POST /api/v1/ai/extract`
Extracts structured attributes from freeform citizen reports.

### `POST /api/v1/ai/precautions`
Generates non-diagnostic citizen precautions.

### `POST /api/v1/ai/response`
Generates role-specific intelligence and staging checklists for Hospital, Police, or Fire responders.

---

## 6. IoT Telemetry Gateway

### `POST /api/v1/iot/events`
Ingests telemetry from ESP32 crash, smoke, and water level sensors. Automatically triggers incidents on critical thresholds.

---

## 7. Multi-Agency CAD Dashboard

### `GET /api/v1/dashboard/overview`
System-wide operational overview including total incidents, readiness percentage, and active nodes.
