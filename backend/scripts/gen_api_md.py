"""Regenerate docs/API.md from the live OpenAPI schema: python scripts/gen_api_md.py > ../docs/API.md"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.main import app  # noqa: E402

AUTH = {"/incidents/{incident_id}/track": "token", "/incidents/{incident_id}/media": "token or role",
        "/incidents/{incident_id}/media/{media_id}/file": "token or role", "/iot/events": "device", "/auth/me": "role"}
spec = app.openapi()
print("# RESQ.AI API reference\n")
print("Generated from the FastAPI OpenAPI schema (`python scripts/gen_api_md.py`). Interactive docs: `/docs`. Base path: `/api/v1`.\n")
print("Auth legend: **public** (no auth), **token** (citizen `X-Tracking-Token` header), **device** (`Authorization: Bearer <IOT_DEVICE_TOKEN>`), **role** (JWT from `/auth/login`).\n")
groups = {}
for path, ops in spec["paths"].items():
    for method, op in ops.items():
        groups.setdefault((op.get("tags") or ["Other"])[0], []).append((method.upper(), path, op))
for tag, items in groups.items():
    print(f"\n## {tag}\n\n| Method | Path | Auth | Summary |\n|---|---|---|---|")
    for m, p, op in items:
        short = p.replace("/api/v1", "")
        auth = AUTH.get(short) or ("role" if short.startswith("/control-room") else "public")
        if short == "/admin/resources/{resource_id}/availability":
            auth = "role (ADMIN or operating org)"
        elif short.startswith("/admin"):
            auth = "role" if "search" in short else "ADMIN"
        summ = (op.get("description") or op.get("summary") or "").strip().split("\n")[0]
        print(f"| {m} | `{short}` | {auth} | {summ} |")
print("\n## WebSocket\n\n`GET /api/v1/ws/control-room?token=<jwt>`: pushes `incident.notification`, `incident.updated` and (ADMIN) `notification.escalated`. "
      "Send `{\"type\":\"delivered\",\"notification_id\":...}` to confirm receipt (the only way a notification becomes DELIVERED).\n")
print("## Errors\n\nAll errors return `{\"detail\": {\"error\": CODE, \"message\": text}}`. Validation errors: 422 with `fields`. Rate limits: 429 `RATE_LIMITED`.\n")
