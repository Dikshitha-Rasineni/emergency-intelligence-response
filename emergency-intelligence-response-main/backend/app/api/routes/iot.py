from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.iot import IoTEventCreate, IoTEventResponse
from app.services.iot_service import IoTService

router = APIRouter()


@router.post("/iot/events", response_model=IoTEventResponse, status_code=status.HTTP_201_CREATED)
def ingest_iot_sensor_event(event: IoTEventCreate, db: Session = Depends(get_db)):
    """
    Ingests ESP32 sensor telemetry (impact, smoke, water, temperature).
    Automatically logs reading and triggers emergency incidents if thresholds are breached.
    """
    return IoTService.ingest_sensor_event(db, event)
