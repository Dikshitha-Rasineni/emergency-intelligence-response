#pragma once

// Copy to include/secrets.h and replace these values. Do not commit secrets.h.
#define RESQ_WIFI_SSID "YOUR_WIFI_SSID"
#define RESQ_WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
#define RESQ_API_BASE_URL "http://192.168.1.10:8000"
// Must match IOT_DEVICE_TOKEN in the backend .env (sent as "Authorization: Bearer ...").
#define RESQ_DEVICE_TOKEN "change-me"
// For https:// deployments, set this to the PEM root CA string for the server.
#define RESQ_ROOT_CA ""

// SIM800L GPRS fallback (only used when ENABLE_SIM800L and GPRS_ALLOW_PLAINTEXT are true in config.h)
#define RESQ_GPRS_APN "your.apn"
#define RESQ_GPRS_USER ""
#define RESQ_GPRS_PASS ""
#define RESQ_GPRS_HOST "your-backend-or-relay.example"  // host only, plain HTTP
#define RESQ_GPRS_PORT 80
