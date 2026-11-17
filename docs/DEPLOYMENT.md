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

## Free cloud demo: Vercel (frontend) + Render (API) + Neon (database)

Vercel serves the React site and forwards `/api/*` to the API (`frontend/vercel.json`), so the browser sees one origin.
WebSockets can't be forwarded by Vercel, so the control room connects to the API directly using `VITE_BACKEND_URL`.

1. **Database (Neon):** create a project at neon.tech (region Singapore). Copy the connection string and change
   `postgresql://` to `postgresql+psycopg://` (keep `?sslmode=require`). PostGIS is enabled by the first migration.
2. **API (Render):** New -> Blueprint -> this repo (uses `render.yaml`). Fill in `DATABASE_URL`, `GEMINI_API_KEY`
   (aistudio.google.com) and `CORS_ORIGINS` (your Vercel URL). Note the service URL, e.g. `https://resq-ai-api.onrender.com`.
   Seed demo data once from the Render Shell: `python -m app.db.seed_demo_data --sample-reports`.
3. **Frontend (Vercel):** Add New -> Project -> this repo. Root Directory: `frontend`. Environment variable
   `VITE_BACKEND_URL` = the Render URL. If the Render URL differs from `resq-ai-api.onrender.com`, edit it in `frontend/vercel.json`.

Free-tier limits: the Render API sleeps after 15 min idle (first request takes ~1 min to wake), and uploaded photos
are lost when it restarts. Fine for a demo or review; use a paid instance with a disk for real use.
