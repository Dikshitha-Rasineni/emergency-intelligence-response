# RESQ.AI — Operational & Technical Workflows

This document details the end-to-end operational, technical, and failure-handling workflows powering the **RESQ.AI** Emergency Intelligence & Decision-Support System.

---

## Table of Contents

1. [Workflow 1: Citizen Emergency Reporting & Multi-Agency Dispatch](#workflow-1-citizen-emergency-reporting--multi-agency-dispatch)
2. [Workflow 2: IoT Sensor Telemetry & Threshold Emergency Ingestion](#workflow-2-iot-sensor-telemetry--threshold-emergency-ingestion)
3. [Workflow 3: Hybrid AI Extraction, Priority Scoring & Safety Guardrails](#workflow-3-hybrid-ai-extraction-priority-scoring--safety-guardrails)
4. [Workflow 4: Geospatial Resource Discovery, Multi-Factor Ranking & Routing](#workflow-4-geospatial-resource-discovery-multi-factor-ranking--routing)
5. [Workflow 5: Role-Specific Tactical Response & Human Verification](#workflow-5-role-specific-tactical-response--human-verification)
6. [Workflow 6: Edge-to-Cloud Fault-Tolerance & Fallback Degradation](#workflow-6-edge-to-cloud-fault-tolerance--fallback-degradation)

---

## Workflow 1: Citizen Emergency Reporting & Multi-Agency Dispatch

```mermaid
sequenceDiagram
    autonumber
    actor Citizen as Citizen / Caller
    participant UI as Citizen Portal (Web)
    participant API as FastAPI Ingestion Layer
    participant AI as Hybrid AI Service (Ollama / Fallback)
    participant Priority as Deterministic Priority Engine
    participant DB as PostgreSQL (SQLAlchemy)
    participant Geo as Geospatial & Amazon Location Service
    actor CAD as Dispatch Supervisor / Responders

    Citizen->>UI: Input emergency description, location name & GPS
    UI->>API: POST /api/v1/incidents
    API->>API: Pydantic Validation (bounds, types, sanitization)
    API->>AI: Extract emergency type, casualties, critical indicators
    alt Ollama Available
        AI-->>API: Structured JSON extraction
    else Ollama Offline or Timeout (>3.0s)
        AI->>AI: Run High-Precision Regex & Keyword Matcher
        AI-->>API: Deterministic extraction fallback
    end
    API->>Priority: Calculate explainable score (0-100) & severity tier
    Priority-->>API: Score, severity (LOW/MODERATE/HIGH/CRITICAL), factors
    API->>DB: Persist Incident, AI Extraction, and Severity Records
    DB-->>API: Generated Incident ID (e.g., INC-D4457C47)
    API->>Geo: Discover nearby resources (Hospitals, Police, Fire)
    Geo->>Geo: Multi-Factor Ranking (Proximity 40%, Capacity 30%, Match 30%)
    Geo-->>API: Ranked emergency resources with ETAs
    API-->>UI: Incident Confirmation, Precautions & Nearby Facilities
    API-)CAD: Real-time Incident Alert on CAD Dashboard
    CAD->>CAD: Verify incident data, review AI guidance, authorize dispatch
```

### Detailed Execution Steps:
1. **Intake & Validation**: The citizen submits free-text details or pre-fills location via browser geolocation (`navigator.geolocation`). Pydantic ensures latitude [-90, 90], longitude [-180, 180], non-negative casualty counts, and sanitizes input strings.
2. **AI Extraction**: The system constructs an extraction prompt with a strict JSON output schema. If Ollama times out or errors, the deterministic fallback engine extracts numbers, casualty mentions, and hazard terms without failing the request.
3. **Scoring**: `PriorityService` calculates a deterministic score using additive rule weights (base 25, unconscious +35, trapped/fire +30, vehicle collision +20, casualty multipliers).
4. **Persistence**: The incident is committed to `emergency_reports`, `ai_extractions`, and `severity_assessments` in a PostgreSQL transaction.
5. **Geospatial Processing**: Nearest resources are fetched and ranked based on Euclidean/road distance, live available capacity, and suitability.
6. **CAD Broadcast**: All operational roles (Hospital, Police, Fire, Admin) view the incoming incident categorized with its severity badge.

---

## Workflow 2: IoT Sensor Telemetry & Threshold Emergency Ingestion

```mermaid
sequenceDiagram
    autonumber
    participant Sensors as Physical Sensors (MPU6050, MQ2, DHT, FSR)
    participant ESP32 as ESP32 Microcontroller
    participant Flash as NVS Flash Storage (Preferences)
    participant WiFi as Network / WiFi
    participant API as FastAPI Backend (/api/v1/iot/events)
    participant IncService as Incident Pipeline
    participant DB as PostgreSQL Database

    loop Every Sensor Polling Cycle
        Sensors->>ESP32: Read Analog/I2C signals (Accel, Smoke, Temp, Force)
        ESP32->>ESP32: Evaluate threshold rules
        alt Impact > 5.0G
            ESP32->>ESP32: Trigger IMPACT emergency event
        else Temp > 60°C or Smoke > 1500 PPM
            ESP32->>ESP32: Trigger FIRE emergency event
        else Water Level > 50 cm
            ESP32->>ESP32: Trigger FLOOD emergency event
        else Heartbeat timer expired (30s)
            ESP32->>ESP32: Trigger ROUTINE TELEMETRY
        end
    end

    alt WiFi Connected
        ESP32->>API: HTTP POST /api/v1/iot/events (JSON payload)
        API->>DB: Store in sensor_readings table
        alt Event is Emergency Trigger
            API->>IncService: Synthesize Emergency Incident
            IncService->>DB: Create Incident Record (source: IOT)
            IncService->>API: Return incident_id and reading_id
        end
        API-->>ESP32: 200 OK (reading_id, incident_id)
    else WiFi Disconnected
        ESP32->>Flash: Enqueue event in Non-Volatile Storage (up to 8 events)
        Note over ESP32,Flash: High-priority emergency events displace routine telemetry
        ESP32->>WiFi: Attempt reconnection (every 10s)
        WiFi-->>ESP32: Connected
        ESP32->>Flash: Read oldest queued event
        ESP32->>API: Drain queued events sequentially
        API-->>ESP32: 200 OK
        ESP32->>Flash: Remove head from queue
    end
```

### Edge Processing Specifics:
- **Impact Sampling Rate**: Accelerometer polled at 100 Hz (10 ms intervals); requires 2 consecutive samples exceeding 5.0 G to filter out transient vibrations.
- **Fire & Smoke**: MQ-2 gas sensor and DHT22 temperature sensor are evaluated simultaneously to detect flaming and smoldering fires.
- **Offline Resilience**: If the field gateway loses connection to the base station, events persist across reboots in ESP32 NVS flash storage. When connectivity is restored, the queue drains automatically in FIFO order.

---

## Workflow 3: Hybrid AI Extraction, Priority Scoring & Safety Guardrails

```mermaid
flowchart TD
    Start(["Unstructured Emergency Text"]) --> CheckRuntime{"Is Ollama Online & Responding < 3.0s?"}
    
    CheckRuntime -- Yes --> LLMCall["Call Ollama API (Model: qwen3:4b / llama3) with JSON Schema"]
    LLMCall --> ValidateJSON{"Valid JSON & adheres to schema?"}
    ValidateJSON -- Yes --> NormalizedData["Normalized Extraction Data"]
    ValidateJSON -- No --> FallbackRegex["Execute High-Precision Deterministic Matcher"]
    
    CheckRuntime -- No --> FallbackRegex
    FallbackRegex --> NormalizedData
    
    NormalizedData --> ScoreEngine["Deterministic Priority & Severity Engine"]
    
    subgraph ScoringRules["Scoring Rules (Additive, Max: 100)"]
        Base["Base Score: 25"]
        Unconscious["Unconscious / Critical: +35"]
        FireTrap["Active Fire / Trapped: +30"]
        Collision["High-Speed Collision: +20"]
        Injuries["Injuries: +5 per injury (max 30)"]
        Casualties["Affected People: +3 per person (max 15)"]
        Hazards["Critical Hazards (Gas/Chemical): +10"]
    end
    
    ScoreEngine --> Compute["Aggregate Score = Base + Sum(Modifiers)"]
    Compute --> BoundedScore["Bound Score: min(100, max(0, Score))"]
    
    BoundedScore --> Tiers{"Score Classification"}
    Tiers -- ">= 75" --> Crit["CRITICAL"]
    Tiers -- "50 - 74" --> High["HIGH"]
    Tiers -- "25 - 49" --> Mod["MODERATE"]
    Tiers -- "< 25" --> Low["LOW"]
    
    Crit & High & Mod & Low --> Guardrails["Apply Safety Guardrails"]
    Guardrails --> AppendDisclaimer["Append Mandatory Non-Diagnostic Disclaimer"]
    AppendDisclaimer --> Output(["Persisted Assessment & Response Directives"])
```

### Safety Principles & Guardrails:
1. **Decision Support Only**: Language models **never** decide final dispatch actions or assign emergency priority directly.
2. **Deterministic Priority**: The 0–100 score is derived strictly through auditable mathematical rules with explicit factor logging.
3. **Non-Diagnostic Constraint**: Medical advice is restricted to standard bystander first-aid staging and trauma center triage alerts.

---

## Workflow 4: Geospatial Resource Discovery, Multi-Factor Ranking & Routing

```mermaid
flowchart LR
    subgraph Input
        IncCoord["Incident Coordinates (Lat, Lng)"]
        IncType["Incident Emergency Type"]
    end

    subgraph Discovery["1. Spatial Discovery"]
        DBQuery["Query PostgreSQL emergency_resources"]
        DistanceCalc["Compute Distance (Haversine & Road Estimates)"]
    end

    subgraph RankingEngine["2. Multi-Factor Ranking Engine"]
        ProxScore["Proximity Score (40% Weight)<br/>Score = max(0, 100 - (Distance_KM * 5))"]
        CapScore["Availability Score (30% Weight)<br/>Score = (Available / Total Capacity) * 100"]
        MatchScore["Suitability Match Score (30% Weight)<br/>Exact Type: 100 | General: 50 | None: 0"]
        Composite["Composite Score = 0.40*Prox + 0.30*Cap + 0.30*Match"]
    end

    subgraph RoutingEngine["3. Dual-Tier Routing Engine"]
        CheckAWS{"Amazon Location Service Configured?"}
        AWSCall["Amazon Location Routes (geo:CalculateRoute)"]
        OSRMCall["OSRM Public Engine (router.project-osrm.org)"]
        LocalGIS["Local Geometric Tortuosity Model (~1.3x Haversine)"]
    end

    IncCoord & IncType --> DBQuery
    DBQuery --> DistanceCalc
    DistanceCalc --> ProxScore & CapScore & MatchScore
    ProxScore & CapScore & MatchScore --> Composite
    Composite --> TopRanked["Ranked Resource Selection"]
    TopRanked --> CheckAWS
    CheckAWS -- "Yes & IAM Valid" --> AWSCall
    CheckAWS -- "Error / Unreachable" --> OSRMCall
    OSRMCall -- "Failure / Offline" --> LocalGIS
    AWSCall & OSRMCall & LocalGIS --> RouteGeo["Decoded Polyline Geometry & Turn-by-Turn ETA"]
```

### Routing Hierarchy:
- **Primary**: **Amazon Location Service Routes** (`geo:CalculateRoute`) providing real-world road network computation, road class restrictions, and high-accuracy vector geometries.
- **Secondary Fallback**: **OSRM Road Routing API** providing open-source road network calculations.
- **Tertiary Fallback**: **Deterministic Haversine + Urban Tortuosity Model** (1.30x distance multiplier @ 40 km/h emergency speed) guaranteeing that zero network or third-party outages will crash the dispatch pipeline.

---

## Workflow 5: Role-Specific Tactical Response & Human Verification

```mermaid
stateDiagram-v2
    [*] --> IncidentReported: Citizen or IoT Event Ingested
    IncidentReported --> TriageVerification: Dispatched to CAD System
    
    state TriageVerification {
        [*] --> PendingReview
        PendingReview --> Acknowledged: CAD Operator Validates Coordinates
        Acknowledged --> Escalated: Critical Multi-Casualty Confirmed
    }
    
    TriageVerification --> RoleDissemination: Auto-generate Role Guidance
    
    state RoleDissemination {
        state HospitalTriage {
            TraumaBayPrep: Reserve Red-Tag Bays
            BloodBankAlert: Stage O-Negative Units
            SurgeonStandby: Alert On-Call Surgical Teams
        }
        state PoliceOperations {
            CorridorLockdown: Clear Priority Transit Route
            PerimeterSecurity: Cordon Hazard Zone (500m)
            TrafficDiverted: Divert Congested Arterials
        }
        state FireAndRescue {
            ExtricationStaging: Heavy Hydraulic Cutters Deployed
            HazmatScan: Thermal & Atmospheric Gas Survey
            BatteryIsolation: EV High-Voltage Disconnect
        }
    }
    
    RoleDissemination --> IncidentResolved: Field Units Complete Action
    IncidentResolved --> [*]
```

---

## Workflow 6: Edge-to-Cloud Fault-Tolerance & Fallback Degradation

| Failure Mode | Primary Path | Fallback Path | Impact on Response Operations |
|---|---|---|---|
| **Ollama Service Down** | Local LLM extraction via HTTP port 11434 | Regex and keyword pattern extraction | **Zero downtime**; extraction falls back to 100% deterministic parsing in < 2ms. |
| **Amazon Location Unavailable** | `geo:CalculateRoute` via AWS IAM | OSRM road API → Local Haversine + 1.3x road tortuosity | **Zero disruption**; dispatchers still receive accurate turn-by-turn route approximations. |
| **PostgreSQL Database Offline** | SQLAlchemy session pool | In-memory cache / Static mock resource bank | System surfaces cached resource markers with operational warnings. |
| **Cellular / WiFi Network Loss** | ESP32 direct HTTP transmission | Non-Volatile Flash FIFO Queue (NVS storage) | Sensor events safely buffered on edge hardware; drained automatically upon reconnection. |
| **Malformed Telemetry / Noise** | Raw ADC readings | Multi-sample confirmation + threshold bounds check | Eliminates transient sensor glitches and false alarms. |
