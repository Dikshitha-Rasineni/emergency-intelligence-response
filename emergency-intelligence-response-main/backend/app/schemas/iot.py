from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class IoTEventCreate(BaseModel):
    device_id: str = Field(..., min_length=2, description="Unique ESP32 device ID")
    event_type: str = Field(default="ACCIDENT", description="Triggered event type: ACCIDENT, FIRE, FLOOD, TELEMETRY")
    temperature: Optional[float] = Field(None, ge=-40.0, le=150.0, description="Temperature in Celsius")
    smoke_level: Optional[float] = Field(None, ge=0.0, le=10000.0, description="Smoke/gas sensor PPM")
    water_level: Optional[float] = Field(None, ge=0.0, le=500.0, description="Water level in cm")
    impact: Optional[float] = Field(None, ge=0.0, le=50.0, description="Impact acceleration in Gs")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    timestamp: Optional[datetime] = None


class IoTEventResponse(BaseModel):
    reading_id: str
    device_id: str
    event_type: str
    status: str
    incident_id: Optional[str] = None
    priority_score: Optional[int] = None
    severity: Optional[str] = None
    message: str
