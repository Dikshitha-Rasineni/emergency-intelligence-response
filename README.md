# RESQ.AI — Emergency Intelligence & Response Support

RESQ.AI turns an emergency report (text, voice, photos, or an ESP32 sensor alert) into one canonical incident. It assesses priority with evidence, routes the incident only to the departments that need it, gives each control room its own English brief, and keeps the citizen informed in English, Telugu, Tamil or Hindi.

> Decision support only. RESQ.AI does not replace 112, official dispatch, or the judgement of trained responders.

**What works and what is untested:** see [docs/STATUS.md](docs/STATUS.md). The audit of the previous version is in [docs/AUDIT.md](docs/AUDIT.md).

## GenAI at the heart of RESQ.AI

Every incident passes through a generative layer (Ollama **Qwen3-4B** for text, **Qwen2.5-VL-3B** for photos):

| Stage | What GenAI does | Technique | Code |
|---|---|---|---|
| Translate | Telugu / Tamil / Hindi report into faithful English (script-checked; MyMemory is only the fallback) | Prompt engineering, structured output | `services/translation_service.py` |
| Understand | Free text into checked facts (type, injuries, trapped, hazards) | Few-shot prompting, JSON-schema output, grounding check, prompt-injection guard | `services/ai_service.py` |
| See | Scene photo into allow-listed findings with confidence | Multimodal (vision-language) | `services/vision_service.py` |
| Brief | For each control room: situation, priority actions, what to prepare, risks, questions to confirm. Sensor-only crashes get their first written account here | Generative reasoning + **RAG** over approved guidance, citations, number-grounding check | `services/genai_service.py` |
| Ask RESQ | Responders ask questions about an incident; answers come only from the record and the guidance, or the model says it does not know | Retrieval-grounded QA | `services/genai_service.py` |
| Guide | Calm, cited safety steps for the citizen in their own language while help arrives | **RAG** + generation + translation | `services/genai_service.py` |

Rules (priority score, routing, nearest unit) stay deterministic and explainable: **the sensor detects, GenAI understands, explains and guides, rules dispatch.**
Every GenAI output is checked: numbers not present in the facts or the guidance are removed, citations must point at retrieved passages,
and if the model is offline a labelled rule-based fallback is shown. The RAG knowledge base (`app/db/knowledge_seed.py`) is a demo compilation
of general first-aid practice, not an official SOP; replace it in Admin -> Knowledge.

**Speed on a laptop.** Briefs are short by design, written once per service in the background the moment an alert
arrives (hospital first), and cached until the facts change. Each brief is about 10–25 s with `qwen3:4b` on an Apple
M-series Mac. For faster briefs: `ollama pull qwen3:1.7b` and set `GENAI_FAST_MODEL=qwen3:1.7b` in `backend/.env`
(extraction keeps the 4B model).

**Hardware:** the in-car unit (ESP32 + force sensor + SIM800L) is in `iot/resq_car_unit/` with wiring, calibration and
a curl test; it posts to `POST /api/v1/iot/sim`.

Endpoints: `GET /api/v1/control-room/incidents/{id}/genai-brief`, `POST /api/v1/control-room/incidents/{id}/ask`,
`GET /api/v1/incidents/{id}/genai-guidance` (citizen, tracking token).

## Quick start (local)

Requirements: Python 3.11+, Node 20+, PostgreSQL 14+ **with PostGIS 3**, optionally [Ollama](https://ollama.com).

```bash
# 1. Database
createdb resq_ai                    # PostGIS is enabled by the migration (CREATE EXTENSION postgis)

# 2. Backend
cd backend
cp .env.example .env                # set DATABASE_URL, JWT_SECRET, IOT_DEVICE_TOKEN, LLM_PROVIDER
pip install -r requirements.txt
alembic upgrade head
python -m app.db.seed_demo_data --sample-reports   # demo accounts + fictional facilities

# 3. Frontend
cd ../frontend && npm install && npm run build   # backend serves frontend/dist

# 4. Run
cd ../backend && uvicorn app.main:app --port 8000
# http://localhost:8000          citizen site
# http://localhost:8000/login    control rooms (demo: fire@resq.demo / resq-demo-2026)
# http://localhost:8000/docs     API
```

Frontend development with hot reload: `cd frontend && npm run dev` (http://localhost:5173, proxies `/api` to :8000).

Docker: `docker compose up --build` (add `--profile ollama` for a local Ollama container).

### Demo accounts (seed only — change before sharing)

| Email | Role |
|---|---|
| admin@resq.demo | ADMIN |
| hospital@resq.demo | HOSPITAL |
| police@resq.demo | POLICE |
| fire@resq.demo | FIRE |
| disaster@resq.demo | DISASTER |

Password: `resq-demo-2026` (override with `SEED_DEMO_PASSWORD`).

## Choosing the AI model (speed)

The citizen never waits for the LLM: the report is stored and assessed by deterministic rules in milliseconds, and the LLM refines it in the background. To make that refinement fast:

| Option | Setting | Notes |
|---|---|---|
| Local Qwen3 (default) | `LLM_PROVIDER=ollama`, `OLLAMA_MODEL=qwen3:4b` | `think:false` is sent automatically (removes the slow reasoning phase); model kept loaded 30 min |
| Smaller local | `OLLAMA_MODEL=qwen3:1.7b` or `qwen2.5:3b` | Faster on CPU, weaker on Telugu/Tamil |
| Hosted, fastest | `LLM_PROVIDER=gemini`, `GEMINI_API_KEY=...` | Good Indian-language quality; also does vision and speech. Reports leave your machine |
| Any OpenAI-compatible | `LLM_PROVIDER=openai` + base URL/key/model | Groq, OpenRouter, or local `llama-server` running Qwen2.5-3B GGUF |

Details: [docs/GENAI.md](docs/GENAI.md).

## Repository layout

```
backend/     FastAPI app, SQLAlchemy models, Alembic migrations, services
frontend/    React + TypeScript + Tailwind + i18next (en/te/ta/hi) + Leaflet
iot/         ESP32 PlatformIO firmware + host tests
testing/     pytest suite (creates its own test database)
docs/        Architecture, API, database, GenAI, multilingual, images, IoT, GSM, RAG, security, testing, deployment
legacy-frontend/   previous vanilla-JS UI (kept for reference, no longer served)
```

## Tests

```bash
cd backend && TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/resq_ai_test python -m pytest ../testing -q
cd iot && g++ -std=c++17 -I include src/hazard_detector.cpp test/host/hazard_detector_test.cpp -o /tmp/h && /tmp/h
cd iot && g++ -std=c++17 -I include test/host/alert_store_test.cpp -o /tmp/a && /tmp/a
cd frontend && npm run build
```

## Documentation

[Architecture](docs/ARCHITECTURE.md) · [Workflow](docs/WORKFLOW.md) · [API](docs/API.md) · [Database](docs/DATABASE.md) · [GenAI](docs/GENAI.md) · [Multilingual](docs/MULTILINGUAL.md) · [Image analysis](docs/IMAGE_ANALYSIS.md) · [IoT](docs/IOT.md) · [GSM](docs/GSM_INTEGRATION.md) · [RAG](docs/RAG.md) · [Security](docs/SECURITY.md) · [Testing](docs/TESTING.md) · [Deployment](docs/DEPLOYMENT.md)

## Live demo: hardware auto-dispatch (Chennai)

1. Reset and seed the demo (Chennai facilities, 3 sensor units, demo logins):
   `cd backend && python -m app.db.seed_demo_data --reset`
2. Start the server: `uvicorn app.main:app --port 8000`
3. Sign in as `admin@resq.demo` (password `resq-demo-2026`) and open **Sensor network** (`/ops`).
4. Press **Crash** on *Crash sensor unit — GST Road*. The alert goes through the same pipeline the ESP32 uses:
   incident created → priority scored → **Hospital + Police (+ Fire for a severe impact)** notified at once.
5. In other browser windows sign in as `hospital@`, `police@`, `fire@resq.demo` to see it arrive live,
   with the sensor reading, the map location and who else was alerted.

Routing for hardware alerts (routing-v1): crash → Hospital + Police (Fire if severe); fire/smoke → Fire + Hospital + Police;
gas → Fire + Hospital + Police; flood → Disaster + Fire + Police. A real ESP32 posts to `POST /api/v1/iot/events`
with `Authorization: Bearer $IOT_DEVICE_TOKEN`.

## Machine translation and unit dispatch

**Translation.** Telugu, Tamil and Hindi reports are machine-translated to English for every control room
within about a second (MyMemory, free, no key), with the configured LLM as fallback, and labelled
"Translated from Telugu · MyMemory machine translation". Facts are also read from the translation, so
injuries, hazards and entrapment are captured even when the LLM is slow. Public notes from responders are
translated back into each reporter's language. `TRANSLATION_PROVIDER=auto|mymemory|llm|none`.

**Dispatch.** 17 demo units (ambulances, fire and rescue tenders, patrols, highway patrol, disaster teams,
rescue boat) are based at the Chennai stations.
- Sensor alerts and HIGH/CRITICAL incidents get the nearest unit of every primary service automatically
  (`AUTO_DISPATCH=true`), with a road-route ETA (OSRM) or a labelled straight-line estimate.
- Control rooms see every unit responding, can dispatch more, change status, cancel, and open a
  **crew phone link** (`/crew/<unit>?t=...`): the crew sees the job, navigates with Google Maps, shares GPS
  and taps On the way → On scene → Transporting → At hospital → Complete.
- Ambulances get the nearest receiving hospital.
- Citizens see "Help on the way" in their language with each unit's live position and minutes remaining.
- Without crew GPS, demo units move along their route (`DEMO_SIMULATE_UNITS=true`, `DEMO_SIM_SPEED=6`),
  clearly labelled as simulated.

After pulling this version: `alembic upgrade head` then `python -m app.db.seed_demo_data --reset`.

## Real Chennai facilities from OpenStreetMap

`python -m app.db.import_osm_facilities` downloads every *named* hospital, fire station, police station and
ambulance station in Chennai (and the GST Road corridor to Chengalpattu) from OpenStreetMap via the Overpass API,
imports them as `data_source=OSM`, moves the demo units to the nearest real station of their kind, points the
demo control rooms at real stations, and removes the fictional facilities they replace (disaster cells and
shelters stay demo because OpenStreetMap does not list them). Availability stays UNKNOWN and phone numbers are
hidden: OpenStreetMap is community data and says where a facility is, not whether it has capacity.

A copy is saved to `datasets/osm_chennai_facilities.json`; later `seed_demo_data --reset` runs re-apply it
offline (`--demo-only` skips it). Data © OpenStreetMap contributors, ODbL.
