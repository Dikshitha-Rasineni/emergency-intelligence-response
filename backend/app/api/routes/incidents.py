from uuid import uuid4

from fastapi import APIRouter, status

from app.schemas.incident import IncidentCreate, IncidentResponse

router = APIRouter()

@router.post("/incidents", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(incident: IncidentCreate):
    incident_id = f"INC-{uuid4().hex[:8].upper()}"

    return IncidentResponse(
        id=incident_id,
        description=incident.description,
        latitude=incident.latitude,
        longitude=incident.longitude,
        affected_people=incident.affected_people,
        injuries=incident.injuries,
        location=incident.location,
        status="reported",
    )
