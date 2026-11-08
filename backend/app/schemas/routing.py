from pydantic import BaseModel, Field
from typing import List, Optional


class RouteRequest(BaseModel):
    origin_lat: float = Field(..., ge=-90.0, le=90.0)
    origin_lng: float = Field(..., ge=-180.0, le=180.0)
    destination_lat: float = Field(..., ge=-90.0, le=90.0)
    destination_lng: float = Field(..., ge=-180.0, le=180.0)
    origin_name: Optional[str] = "Station"
    destination_name: Optional[str] = "Incident location"
    responder_role: Optional[str] = None


class RouteStep(BaseModel):
    instruction: str
    distance_km: float
    duration_min: float


class RouteResponse(BaseModel):
    available: bool
    provider: str                       # AMAZON_LOCATION | OSRM | UNAVAILABLE
    message: Optional[str] = None
    origin_name: str
    destination_name: str
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    distance_km: Optional[float] = None  # road distance from provider; None when unavailable
    eta_min: Optional[int] = None        # provider's normal-traffic duration; None when unavailable
    eta_note: Optional[str] = None
    straight_line_km: float              # always computed, clearly labelled
    route_corridor: Optional[str] = None
    steps: List[RouteStep] = Field(default_factory=list)
    coordinates: List[List[float]] = Field(default_factory=list)  # [[lat,lng],...] provider geometry only
    routing_status: str                  # kept for older clients
