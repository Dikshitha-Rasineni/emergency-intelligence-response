# Deployment

**Docker files were written but not run in the build environment.**

## Docker Compose (single host)

```bash
cp backend/.env.example backend/.env    # set JWT_SECRET, IOT_DEVICE_TOKEN, LLM_PROVIDER, APP_ENV=production
docker compose up --build -d
docker compose exec api python -m app.db.seed_demo_data   # optional demo data
```
With local models: `docker compose --profile ollama up -d`, then `docker compose exec ollama ollama pull qwen3:4b` and `ollama pull qwen2.5vl:3b`. CPU inference is slow for vision; use a GPU host or Gemini for demos.

## Production checklist

- HTTPS reverse proxy (Caddy/nginx) in front of port 8000; WebSocket upgrade enabled for `/api/v1/ws/`.
- `APP_ENV=production` (refuses default JWT secret and missing device token).
- Managed PostgreSQL with PostGIS; daily backups; `alembic upgrade head` on deploy (done by the container command).
- Persistent volume for `uploads/`; schedule `POST /api/v1/admin/media/purge` daily.
- Self-host OSRM with an India extract instead of the public demo server.
- One API worker unless rate limiting/WebSockets are moved to Redis.
- Monitoring: `GET /api/v1/health` (database, PostGIS, AI provider reachability); logs include request ID and latency.
