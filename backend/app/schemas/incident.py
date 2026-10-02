from pydantic import BaseModel, Field
from typing import Optional

class IncidentCreate(BaseModel):
    description: str = Field(..., min_length=5)
    latitude: float
    longitude: float
    affected_people: int = Field(default=0, ge=0)
    injuries: int = Field(default=0, ge=0)
    location: Optional[str] = None

class IncidentResponse(IncidentCreate):
    id: str
    status: str
