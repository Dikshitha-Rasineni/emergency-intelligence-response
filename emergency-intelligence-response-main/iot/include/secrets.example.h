#pragma once

// Copy to include/secrets.h and replace these values. Do not commit secrets.h.
#define RESQ_WIFI_SSID "YOUR_WIFI_SSID"
#define RESQ_WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
#define RESQ_API_BASE_URL "http://192.168.1.10:8000"
// The current FastAPI IoT route does not enforce authentication. A configured
// token is sent as Bearer only for a future/auth-enabled deployment.
#define RESQ_DEVICE_TOKEN ""
// For https:// deployments, set this to the PEM root CA string for the server.
#define RESQ_ROOT_CA ""
