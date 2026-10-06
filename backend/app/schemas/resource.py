from pydantic import BaseModel
from typing import Optional


class ResourceAvailabilityResponse(BaseModel):
    available_units: int
    status: str
    wait_time_minutes: int


class ResourceResponse(BaseModel):
    id: str
    name: str
    resource_type: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    contact_number: Optional[str] = None

    available_units: int
    availability_status: str
    wait_time_minutes: int

    distance_km: float