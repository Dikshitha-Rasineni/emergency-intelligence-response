# RESQ.AI API reference

Generated from the FastAPI OpenAPI schema (`python scripts/gen_api_md.py`). Interactive docs: `/docs`. Base path: `/api/v1`.

Auth legend: **public** (no auth), **token** (citizen `X-Tracking-Token` header), **device** (`Authorization: Bearer <IOT_DEVICE_TOKEN>`), **role** (JWT from `/auth/login`).


## Health

| Method | Path | Auth | Summary |
|---|---|---|---|
| GET | `/health` | public | Health Check |
| GET | `/meta` | public | Meta |

## Auth

| Method | Path | Auth | Summary |
|---|---|---|---|
| POST | `/auth/login` | public | Login |
| GET | `/auth/me` | role | Me |

## Citizen incidents

| Method | Path | Auth | Summary |
|---|---|---|---|
| POST | `/incidents` | public | Submit an emergency report. Returns immediately with a rule-based assessment; |
| GET | `/incidents/{incident_id}/track` | token | Track Incident |
| POST | `/incidents/{incident_id}/media` | token or role | Attach 1..N images. Each is validated, cleaned (EXIF stripped) and analysed in the background. |
| GET | `/incidents/{incident_id}/media` | token or role | List Media |
| GET | `/incidents/{incident_id}/media/{media_id}/file` | token or role | Get Media File |

## Control room

| Method | Path | Auth | Summary |
|---|---|---|---|
| GET | `/control-room/incidents` | role | List Incidents |
| GET | `/control-room/summary` | role | Summary |
| GET | `/control-room/incidents/{incident_id}` | role | Get Incident |
| POST | `/control-room/incidents/{incident_id}/acknowledge` | role | Acknowledge |
| POST | `/control-room/incidents/{incident_id}/status` | role | Update Status |
| POST | `/control-room/incidents/{incident_id}/priority-override` | role | Authorized assessment override. Recorded as a new assessment with the user and reason. |
| POST | `/control-room/notifications/{notification_id}/delivered` | role | Confirm Delivery |

## Admin

| Method | Path | Auth | Summary |
|---|---|---|---|
| GET | `/admin/users` | ADMIN | List Users |
| POST | `/admin/users` | ADMIN | Create User |
| POST | `/admin/users/{user_id}/active` | ADMIN | Set User Active |
| GET | `/admin/organizations` | ADMIN | List Orgs |
| POST | `/admin/organizations` | ADMIN | Create Org |
| GET | `/admin/resources` | ADMIN | List Resources |
| POST | `/admin/resources` | ADMIN | Upsert Resource |
| DELETE | `/admin/resources/{resource_id}` | ADMIN | Delete Resource |
| POST | `/admin/resources/{resource_id}/availability` | role (ADMIN or operating org) | Admins, or users of the organisation that operates this resource, may report availability. |
| GET | `/admin/devices` | ADMIN | List Devices |
| POST | `/admin/devices` | ADMIN | Upsert Device |
| GET | `/admin/knowledge` | ADMIN | List Docs |
| POST | `/admin/knowledge` | ADMIN | Add Doc |
| POST | `/admin/knowledge/{doc_id}/approve` | ADMIN | Approve Doc |
| DELETE | `/admin/knowledge/{doc_id}` | ADMIN | Delete Doc |
| GET | `/admin/knowledge/search` | role | Search Docs |
| GET | `/admin/audit` | ADMIN | Audit |
| GET | `/admin/config` | ADMIN | Config |
| POST | `/admin/media/purge` | ADMIN | Deletes stored images past their retention date (MEDIA_RETENTION_DAYS). |

## Resources

| Method | Path | Auth | Summary |
|---|---|---|---|
| GET | `/resources/nearby` | public | Nearby facilities via PostGIS. Distances are straight-line; availability is UNKNOWN unless reported. |
| POST | `/resources/rank` | public | Rank Resources |
| GET | `/resources/geocode` | public | Geocode Location |

## Routing

| Method | Path | Auth | Summary |
|---|---|---|---|
| GET | `/routes` | public | Computes verified routing metrics, road distance, ETA, waypoints, and navigation steps. |
| POST | `/routes` | public | POST variant of route calculation. |

## AI utilities

| Method | Path | Auth | Summary |
|---|---|---|---|
| POST | `/ai/extract` | public | Structured extraction (LLM if configured, otherwise rule-based). Rate limited. |
| POST | `/ai/precautions` | public | Generates non-diagnostic citizen precautions tailored to the emergency type. |
| POST | `/ai/response` | public | Generates tactical decision support for Hospital, Police, or Fire responders. |

## IoT

| Method | Path | Auth | Summary |
|---|---|---|---|
| POST | `/iot/events` | device | ESP32 telemetry and qualified alerts. 201 = stored; 200 = duplicate event_id (already stored). |

## Speech

| Method | Path | Auth | Summary |
|---|---|---|---|
| POST | `/speech/transcribe` | public | Server-side speech-to-text (used when the browser has no speech recognition for the language). |

## Amazon Location maps

| Method | Path | Auth | Summary |
|---|---|---|---|
| GET | `/maps/style.json` | public | Proxy the MapLibre style descriptor from Amazon Location. |
| GET | `/maps/tiles/{z}/{x}/{y}` | public | Proxy vector map tile from Amazon Location. |
| GET | `/maps/glyphs/{font_stack}/{font_range}.pbf` | public | Proxy map glyphs from Amazon Location. |
| GET | `/maps/sprites/{filename}` | public | Proxy map sprites from Amazon Location. |

## WebSocket

`GET /api/v1/ws/control-room?token=<jwt>`: pushes `incident.notification`, `incident.updated` and (ADMIN) `notification.escalated`. Send `{"type":"delivered","notification_id":...}` to confirm receipt (the only way a notification becomes DELIVERED).

## Errors

All errors return `{"detail": {"error": CODE, "message": text}}`. Validation errors: 422 with `fields`. Rate limits: 429 `RATE_LIMITED`.

