import asyncio
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.exceptions import AppException, app_exception_handler
from app.core.logging import setup_logging, logger
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.control_room import router as control_room_router
from app.api.routes.admin import router as admin_router
from app.api.routes.resources import router as resources_router
from app.api.routes.routing import router as routing_router
from app.api.routes.ai import router as ai_router
from app.api.routes.iot import router as iot_router
from app.api.routes.speech import router as speech_router
from app.api.routes.maps import router as maps_router
from app.api.routes.dispatch import router as dispatch_router
from app.services.realtime import manager

setup_logging()


async def _escalation_loop():
    from app.db.session import SessionLocal
    from app.services.notification_service import NotificationService
    while True:
        await asyncio.sleep(30)
        def run():
            db = SessionLocal()
            try:
                NotificationService.run_escalations(db)
            finally:
                db.close()
        try:
            await asyncio.to_thread(run)
        except Exception as e:
            logger.warning(f"escalation loop error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    manager.loop = asyncio.get_running_loop()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    if settings.APP_ENV == "production" and settings.JWT_SECRET.startswith("change-me"):
        raise RuntimeError("Set JWT_SECRET in production.")
    task = asyncio.create_task(_escalation_loop()) if settings.APP_ENV != "test" else None
    yield
    if task:
        task.cancel()


app = FastAPI(title=settings.PROJECT_NAME, version="2.0.0", lifespan=lifespan,
              description="RESQ.AI emergency decision-support API. Not a replacement for official dispatch systems.",
              docs_url="/docs", redoc_url="/redoc")
app.add_exception_handler(AppException, app_exception_handler)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": {"error": "VALIDATION_ERROR", "message": "Invalid request.",
                                                             "fields": [{"loc": e.get("loc"), "msg": e.get("msg")} for e in exc.errors()]}})


@app.middleware("http")
async def request_context(request: Request, call_next):
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    start = time.perf_counter()
    response = await call_next(request)
    ms = int((time.perf_counter() - start) * 1000)
    response.headers["X-Request-ID"] = rid
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    if request.url.path.startswith("/api/"):
        # Path + status + latency only: never log bodies (citizen data).
        logger.info(f"req={rid} {request.method} {request.url.path} status={response.status_code} ms={ms}")
    return response


app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True,
                   allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["*"])

API = settings.API_V1_STR
for r, tag in ((health_router, "Health"), (auth_router, "Auth"), (incidents_router, "Citizen incidents"),
               (control_room_router, "Control room"), (admin_router, "Admin"), (resources_router, "Resources"),
               (routing_router, "Routing"), (ai_router, "AI utilities"), (iot_router, "IoT"),
               (speech_router, "Speech"), (maps_router, "Amazon Location maps"), (dispatch_router, "Unit dispatch")):
    app.include_router(r, prefix=API, tags=[tag])

# ---- Serve the built React frontend (single origin: no CORS needed in production)
DIST = os.path.realpath(settings.FRONTEND_DIST)
if os.path.isdir(DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith(("api/", "docs", "redoc", "openapi.json")):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        candidate = os.path.realpath(os.path.join(DIST, full_path))
        if full_path and candidate.startswith(DIST) and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(DIST, "index.html"))
else:
    @app.get("/", include_in_schema=False)
    def root():
        return {"system": "RESQ.AI API", "docs": "/docs", "frontend": "not built (run npm run build in frontend/)"}
