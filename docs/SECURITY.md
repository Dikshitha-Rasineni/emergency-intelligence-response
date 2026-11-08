# Security and privacy

| Control | Implementation |
|---|---|
| Authentication | JWT (HS256, `JWT_SECRET`, 8 h expiry); passwords PBKDF2-SHA256 240k iterations; login rate-limited; failed logins audited |
| Roles | ADMIN, HOSPITAL, POLICE, FIRE, DISASTER (`require_roles`) |
| Incident access | Department users see only incidents currently routed to them; others get 404 (no existence leak) |
| Field-level filtering | `DEPARTMENT_FIELDS` + per-department image-finding filter; original citizen text only for ADMIN |
| Citizen access | Random 24-byte tracking token, only its SHA-256 stored, sent in `X-Tracking-Token` header (not URLs) |
| Devices | Shared bearer token `IOT_DEVICE_TOKEN`; production refuses to start the endpoint without it |
| Availability data | Only ADMIN or the organisation operating a resource can report availability |
| Uploads | Size/type/decode validation, re-encode (strips EXIF/GPS), private storage path checks, `nosniff`, `no-store`, retention purge |
| Prompt injection | Untrusted text wrapped and labelled; model outputs validated against allow-lists; models cannot trigger routing, notification or permissions |
| Rate limiting | Per-IP sliding window on reports, uploads, AI utilities, speech, login (in-process) |
| Logging | Request path, status, latency, request ID only; no bodies |
| Audit | Logins, views, status changes, overrides, acknowledgements, admin changes, IoT alerts, purges |
| Headers | `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy` |
| Secrets | `.env` and `iot/include/secrets.h` git-ignored; production refuses the default JWT secret |

## Before any real deployment

- Serve over HTTPS (reverse proxy) and restrict CORS to your origin.
- Replace demo accounts; enforce password rotation/MFA at the identity layer if available.
- Per-device tokens instead of one shared token; move rate limiting and WebSockets to Redis for multiple workers.
- Legal review of data retention and of sending data to hosted AI providers (DPDP Act 2023 in India).
