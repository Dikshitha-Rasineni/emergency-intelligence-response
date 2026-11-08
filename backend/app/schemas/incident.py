from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    description: str = Field(..., min_length=3, max_length=4000, description="Report in any language, as typed or transcribed")
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    location_source: Optional[str] = Field(None, description="DEVICE_GPS | MANUAL_PIN")
    location_accuracy_m: Optional[float] = Field(None, ge=0, le=100000)
    location: Optional[str] = Field(None, max_length=255, description="Landmark / address text")
    location_name: Optional[str] = Field(None, max_length=255)
    language: Optional[str] = Field(None, max_length=10, description="Input language if known; 'auto' or omit to detect")
    preferred_language: Optional[str] = Field(None, max_length=10, description="Language for citizen-facing responses")
    emergency_type: Optional[str] = Field(None, max_length=40, description="Optional category chosen by the citizen")
    affected_people: int = Field(default=0, ge=0, le=10000)
    injuries: int = Field(default=0, ge=0, le=10000)
    # Accepted for backward compatibility and ignored: citizens cannot set the system priority.
    user_priority: Optional[int] = Field(None, ge=0, le=100)
    critical_indicators: Optional[List[str]] = None
    source: Optional[str] = None


class IncidentCreated(BaseModel):
    incident_id: str
    tracking_token: str = Field(..., description="Shown once. Needed to track the report and add photos.")
    merged_into: Optional[str] = None
    citizen_view: Dict[str, Any]


class StatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(ACKNOWLEDGED|RESPONDING|ON_SCENE|RESOLVED|CLOSED|FALSE_ALARM)$")
    note: Optional[str] = Field(None, max_length=1000)
    public: bool = Field(False, description="Show this update to the citizen tracker")


class PriorityOverride(BaseModel):
    score: int = Field(..., ge=0, le=100)
    reason: str = Field(..., min_length=5, max_length=500)


class Page(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[Dict[str, Any]]
