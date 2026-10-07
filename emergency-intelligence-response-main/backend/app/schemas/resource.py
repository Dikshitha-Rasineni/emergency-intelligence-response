from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ResourceAvailabilitySchema(BaseModel):
    available_units: int
    wait_time: int
    status: str
    operational_details: Dict[str, Any] = Field(default_factory=dict)


class ResourceResponse(BaseModel):
    id: str
    resource_id: str  # alias
    name: str
    type: str  # HOSPITAL, AMBULANCE, POLICE, FIRE
    resource_type: str
    latitude: float
    longitude: float
    lat: float  # alias
    lng: float  # alias
    address: Optional[str] = None
    phone: Optional[str] = None
    contact: Optional[str] = None  # alias
    capabilities: List[str]
    capability: Optional[str] = None  # formatted summary string
    availability: str  # e.g. "Available" or "Emergency Department Available"
    available_units: int
    wait_time: int
    distance_km: Optional[float] = None
    eta_min: Optional[int] = None
    suitability_score: Optional[float] = None
    ranking: Optional[int] = None
    operational_details: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class ResourceRankRequest(BaseModel):
    incident_id: Optional[str] = None
    latitude: float
    longitude: float
    emergency_type: str
    injuries: int = 0
    affected_people: int = 0
    max_radius_km: float = 25.0


class ResourceRankResponse(BaseModel):
    total_found: int
    resources: List[ResourceResponse]
