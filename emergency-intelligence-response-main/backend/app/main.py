from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import AppException, app_exception_handler

from app.api.routes.health import router as health_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.resources import router as resources_router
from app.api.routes.routing import router as routing_router
from app.api.routes.ai import router as ai_router
from app.api.routes.iot import router as iot_router
from app.api.routes.dashboard import router as dashboard_router

setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Operational Decision-Support and Dispatch Intelligence API for RESQ.AI.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Exception handling
app.add_exception_handler(AppException, app_exception_handler)

# CORS configuration
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]
if isinstance(settings.CORS_ORIGINS, list):
    allowed_origins = list(set(allowed_origins + settings.CORS_ORIGINS))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. API v1 Routers (Canonical Specification)
app.include_router(health_router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(incidents_router, prefix=settings.API_V1_STR, tags=["Incidents"])
app.include_router(resources_router, prefix=settings.API_V1_STR, tags=["Resources"])
app.include_router(routing_router, prefix=settings.API_V1_STR, tags=["Routing"])
app.include_router(ai_router, prefix=settings.API_V1_STR, tags=["AI Decision Support"])
app.include_router(iot_router, prefix=settings.API_V1_STR, tags=["IoT Gateways"])
app.include_router(dashboard_router, prefix=settings.API_V1_STR, tags=["Dashboard"])

# 2. Backward Compatibility Aliases (/api and root)
app.include_router(health_router, prefix="/api", tags=["Aliases"])
app.include_router(incidents_router, prefix="/api", tags=["Aliases"])
app.include_router(resources_router, prefix="/api", tags=["Aliases"])
app.include_router(routing_router, prefix="/api", tags=["Aliases"])
app.include_router(ai_router, prefix="/api", tags=["Aliases"])
app.include_router(health_router, tags=["Aliases"])
app.include_router(incidents_router, tags=["Aliases"])


@app.get("/")
def root():
    return {
        "system": "RESQ.AI Operational Emergency Intelligence API",
        "status": "ONLINE",
        "api_docs": "/docs",
        "version": "1.0.0",
    }