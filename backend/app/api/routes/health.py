from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.services import llm_provider
from app.services.realtime import manager
from app.services.taxonomy import CATEGORIES, CATEGORY_LABELS_EN, SUPPORTED_UI_LANGUAGES

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_status, postgis = "connected", None
    try:
        db.execute(text("SELECT 1"))
        postgis = db.execute(text("SELECT extversion FROM pg_extension WHERE extname='postgis'")).scalar()
    except Exception as e:
        db_status = f"unhealthy: {type(e).__name__}"
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "resq-ai-backend",
        "database": db_status,
        "postgis": postgis or "missing",
        "ai": llm_provider.provider_status(),
        "routing": {"provider_order": (["AMAZON_LOCATION"] if settings.AWS_LOCATION_ROUTE_CALCULATOR else []) + ["OSRM"],
                    "osrm_base_url": settings.OSRM_BASE_URL},
        "iot_device_auth": "enabled" if settings.IOT_DEVICE_TOKEN else "disabled (development)",
        "websocket_connections": {k: len(v) for k, v in manager.by_dept.items()},
    }


@router.get("/meta")
def meta():
    return {"categories": [{"code": c, "label": CATEGORY_LABELS_EN[c]} for c in CATEGORIES],
            "ui_languages": list(SUPPORTED_UI_LANGUAGES),
            "speech_server_available": settings.STT_PROVIDER.lower() != "none",
            "max_image_mb": settings.MAX_IMAGE_MB, "max_images": settings.MAX_IMAGES_PER_INCIDENT,
            "emergency_number": "112"}
