from pydantic import BaseModel, Field
from typing import List, Optional


class RouteRequest(BaseModel):
    origin_lat: float = Field(..., ge=-90.0, le=90.0)
    origin_lng: float = Field(..., ge=-180.0, le=180.0)
    destination_lat: float = Field(..., ge=-90.0, le=90.0)
    destination_lng: float = Field(..., ge=-180.0, le=180.0)
    origin_name: Optional[str] = "Station Base"
    destination_name: Optional[str] = "Incident Location"
    responder_role: Optional[str] = None  # HOSPITAL, POLICE, FIRE


class RouteStep(BaseModel):
    instruction: str
    distance_km: float
    duration_min: float


class RouteResponse(BaseModel):
    origin_name: str
    destination_name: str
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    distance_km: float
    eta_min: int
    route_corridor: str
    steps: List[RouteStep]
    coordinates: List[List[float]]  # [[lat, lng], [lat, lng], ...] for Leaflet polyline
    routing_status: str = "GIS_CALCULATED"
