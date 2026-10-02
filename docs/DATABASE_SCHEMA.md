# Database Schema

## Database

PostgreSQL + PostGIS

---

## 1. users

Stores system users and their roles.

| Field | Type | Description |
|---|---|---|
| id | UUID | Unique user ID |
| name | VARCHAR | User name |
| email | VARCHAR | User email |
| role | VARCHAR | citizen / responder / admin |
| created_at | TIMESTAMP | Account creation time |

---

## 2. emergency_reports

Stores reported emergency incidents.

| Field | Type | Description |
|---|---|---|
| id | UUID | Unique incident ID |
| description | TEXT | Emergency description |
| latitude | DECIMAL | Incident latitude |
| longitude | DECIMAL | Incident longitude |
| location | VARCHAR | Location description |
| affected_people | INTEGER | Number of affected people |
| injuries | INTEGER | Number of injured people |
| status | VARCHAR | Incident status |
| created_at | TIMESTAMP | Report time |

---

## 3. ai_extractions

Stores structured information extracted from emergency reports.

| Field | Type | Description |
|---|---|---|
| id | UUID | Unique extraction ID |
| incident_id | UUID | Related incident |
| emergency_type | VARCHAR | Type of emergency |
| affected_people | INTEGER | Extracted affected people |
| injuries | INTEGER | Extracted injuries |
| critical_indicators | JSONB | Critical indicators |
| location_information | TEXT | Extracted location information |
| created_at | TIMESTAMP | Extraction time |

---

## 4. severity_assessments

Stores severity and priority assessment results.

| Field | Type | Description |
|---|---|---|
| id | UUID | Unique assessment ID |
| incident_id | UUID | Related incident |
| severity | VARCHAR | Severity level |
| priority_score | DECIMAL | Priority score |
| factors | JSONB | Factors used for assessment |
| created_at | TIMESTAMP | Assessment time |

---

## 5. emergency_resources

Stores available emergency resources.

| Field | Type | Description |
|---|---|---|
| id | UUID | Unique resource ID |
| name | VARCHAR | Resource name |
| resource_type | VARCHAR | hospital / ambulance / fire_station / police / shelter |
| latitude | DECIMAL | Resource latitude |
| longitude | DECIMAL | Resource longitude |
| address | TEXT | Resource address |
| created_at | TIMESTAMP | Record creation time |

---

## 6. resource_availability

Stores current resource availability.

| Field | Type | Description |
|---|---|---|
| id | UUID | Unique availability ID |
| resource_id | UUID | Related resource |
| available_units | INTEGER | Available units |
| wait_time | INTEGER | Estimated wait time |
| status | VARCHAR | Available / busy / unavailable |
| updated_at | TIMESTAMP | Last update time |

---

## 7. incident_resources

Stores resources associated with an incident.

| Field | Type | Description |
|---|---|---|
| id | UUID | Unique record ID |
| incident_id | UUID | Related incident |
| resource_id | UUID | Related resource |
| distance | DECIMAL | Distance from incident |
| suitability_score | DECIMAL | Resource suitability |
| ranking | INTEGER | Resource ranking |
| assigned_at | TIMESTAMP | Assignment time |

---

## 8. sensor_readings

Stores IoT sensor data received from ESP32 devices.

| Field | Type | Description |
|---|---|---|
| id | UUID | Unique reading ID |
| device_id | VARCHAR | ESP32 device ID |
| temperature | DECIMAL | Temperature reading |
| smoke_level | DECIMAL | Smoke sensor reading |
| water_level | DECIMAL | Water level |
| impact | DECIMAL | Impact reading |
| latitude | DECIMAL | Sensor latitude |
| longitude | DECIMAL | Sensor longitude |
| timestamp | TIMESTAMP | Sensor reading time |

---

## 9. response_recommendations

Stores generated emergency response recommendations.

| Field | Type | Description |
|---|---|---|
| id | UUID | Unique recommendation ID |
| incident_id | UUID | Related incident |
| summary | TEXT | Emergency summary |
| recommendation | TEXT | Recommended response |
| explanation | TEXT | Explanation |
| missing_information | JSONB | Missing information alerts |
| created_at | TIMESTAMP | Recommendation time |

---

## Relationships

- `emergency_reports` → `ai_extractions`
- `emergency_reports` → `severity_assessments`
- `emergency_reports` → `incident_resources`
- `emergency_resources` → `resource_availability`
- `emergency_resources` → `incident_resources`
- `emergency_reports` → `response_recommendations`
- `sensor_readings` → emergency incidents through location/time correlation
- `users` → emergency reports through the reporting user relationship

---

## Geospatial Support

PostGIS will be used for:

- Incident coordinates
- Resource coordinates
- Nearby resource search
- Distance calculation
- Geographic filtering
- Map-based visualization