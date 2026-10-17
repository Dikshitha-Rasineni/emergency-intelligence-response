from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class IncidentCreate(BaseModel):
    description: str = Field(..., min_length=5, description="Unstructured description of the emergency")
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0, description="GPS Latitude")
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0, description="GPS Longitude")
    location: Optional[str] = Field(None, description="Landmark or road location description")
    location_name: Optional[str] = Field(None, description="Frontend alias for location")
    language: Optional[str] = Field(None, description="Preferred or detected input language")
    affected_people: int = Field(default=0, ge=0)
    injuries: int = Field(default=0, ge=0)
    critical_indicators: Optional[List[str]] = Field(default_factory=list)
    emergency_type: Optional[str] = Field(None)
    user_priority: Optional[int] = Field(None, ge=0, le=100)
    source: str = Field(default="USER")


class IncidentUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None
    affected_people: Optional[int] = None
    injuries: Optional[int] = None
    user_priority: Optional[int] = None
    location: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    language: Optional[str] = None


class IncidentResponse(BaseModel):
    incident_id: str
    id: str  # alias for frontend compatibility
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: str
    location: Optional[str] = None
    location_source: Optional[str] = "USER_ENTERED"
    coordinates_verified: bool = True
    detected_language: str = "en"
    language: str = "en"
    affected_people: int
    injuries: int
    critical_indicators: List[str]
    emergency_type: str
    priority_score: int
    system_priority: int  # alias for frontend
    user_priority: int
    severity: str
    status: str
    source: str
    created_at: datetime
    updated_at: datetime
    precautions: Optional[List[str]] = None
    recommendations: Optional[dict] = None

    model_config = {"from_attributes": True}


class IncidentListResponse(BaseModel):
    total: int
    incidents: List[IncidentResponse]
