from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ResourceResponse(BaseModel):
    id: str
    resource_id: str
    name: str
    type: str  # HOSPITAL, AMBULANCE, POLICE, FIRE, SHELTER, DISASTER
    resource_type: str
    latitude: float
    longitude: float
    lat: float
    lng: float
    address: Optional[str] = None
    phone: Optional[str] = None  # None when not verified/listed
    capabilities: List[str] = Field(default_factory=list)
    availability: str = "Unknown"          # human label; "Unknown" unless reported by an authorized user
    availability_status: str = "UNKNOWN"   # AVAILABLE | BUSY | OFFLINE | UNKNOWN
    availability_verified: bool = False
    availability_updated_at: Optional[str] = None
    available_units: Optional[int] = None
    distance_km: Optional[float] = None
    distance_type: str = "straight_line"   # road distance only comes from the routing endpoint
    suitability_score: Optional[float] = None
    ranking: Optional[int] = None
    provider: str = "RESQ.AI resource registry"
    data_source: str = "ADMIN"             # ADMIN | DEMO_SEED | OSM
    verified: bool = False
    retrieved_at: Optional[str] = None
    navigation_url: Optional[str] = None


class ResourceUpsert(BaseModel):
    id: Optional[str] = Field(None, max_length=50)
    name: str = Field(..., min_length=2, max_length=150)
    resource_type: str = Field(..., pattern="^(HOSPITAL|AMBULANCE|POLICE|FIRE|SHELTER|DISASTER)$")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)
    capabilities: List[str] = Field(default_factory=list)
    verified: bool = False


class AvailabilityUpdate(BaseModel):
    status: str = Field(..., pattern="^(AVAILABLE|BUSY|OFFLINE|UNKNOWN)$")
    available_units: Optional[int] = Field(None, ge=0, le=10000)
    operational_details: Dict[str, Any] = Field(default_factory=dict)


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
