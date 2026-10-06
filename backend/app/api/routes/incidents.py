from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import EmergencyReport
from app.schemas.incident import IncidentCreate, IncidentResponse

router = APIRouter()


@router.post(
    "/incidents",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_incident(
    incident: IncidentCreate,
    db: Session = Depends(get_db),
):
    emergency_report = EmergencyReport(
        description=incident.description,
        latitude=incident.latitude,
        longitude=incident.longitude,
        location=incident.location,
        affected_people=incident.affected_people,
        injuries=incident.injuries,
        status="reported",
    )

    db.add(emergency_report)
    db.commit()
    db.refresh(emergency_report)

    return IncidentResponse(
        id=emergency_report.id,
        description=emergency_report.description,
        latitude=emergency_report.latitude,
        longitude=emergency_report.longitude,
        affected_people=emergency_report.affected_people,
        injuries=emergency_report.injuries,
        location=emergency_report.location,
        status=emergency_report.status,
        created_at=emergency_report.created_at,
    )


@router.get("/incidents", response_model=list[IncidentResponse])
def get_incidents(db: Session = Depends(get_db)):
    incidents = (
        db.query(EmergencyReport)
        .order_by(EmergencyReport.created_at.desc())
        .all()
    )

    return [
        IncidentResponse(
            id=incident.id,
            description=incident.description,
            latitude=incident.latitude,
            longitude=incident.longitude,
            affected_people=incident.affected_people,
            injuries=incident.injuries,
            location=incident.location,
            status=incident.status,
            created_at=incident.created_at,
        )
        for incident in incidents
    ]


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: str,
    db: Session = Depends(get_db),
):
    incident = (
        db.query(EmergencyReport)
        .filter(EmergencyReport.id == incident_id)
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return IncidentResponse(
        id=incident.id,
        description=incident.description,
        latitude=incident.latitude,
        longitude=incident.longitude,
        affected_people=incident.affected_people,
        injuries=incident.injuries,
        location=incident.location,
        status=incident.status,
        created_at=incident.created_at,
    )