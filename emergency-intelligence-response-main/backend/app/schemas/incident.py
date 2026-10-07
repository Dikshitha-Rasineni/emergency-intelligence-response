from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class IncidentCreate(BaseModel):
    description: str = Field(..., min_length=5, description="Unstructured description of the emergency")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="GPS Latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="GPS Longitude")
    location: Optional[str] = Field(None, description="Landmark or road location description")
    location_name: Optional[str] = Field(None, description="Frontend alias for location")
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


class IncidentResponse(BaseModel):
    incident_id: str
    id: str  # alias for frontend compatibility
    description: str
    latitude: float
    longitude: float
    location_name: str
    location: Optional[str] = None
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
