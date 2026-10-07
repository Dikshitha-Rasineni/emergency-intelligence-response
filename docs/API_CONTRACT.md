# API Contract

## Base URL

`http://127.0.0.1:8000`

---

## 1. Health Check

### GET `/api/health`

Checks whether the backend is running.

### Response

```json
{
  "status": "healthy",
  "service": "backend"
}
