from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.incident import IncidentCreate, IncidentUpdate, IncidentResponse
from app.services.incident_service import IncidentService
from app.models.incident import EmergencyReport

router = APIRouter()


@router.post("/incidents", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    """
    Submits a new emergency incident.
    Performs AI extraction, priority scoring, nearby resource association, and persists all records.
    """
    return IncidentService.create_incident(db, incident)


@router.get("/incidents", response_model=List[IncidentResponse])
def list_incidents(limit: int = 50, db: Session = Depends(get_db)):
    """
    Retrieves active and recent incidents.
    """
    return IncidentService.list_incidents(db, limit=limit)


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    """
    Retrieves full details for a single incident including AI analysis, precautions, and resources.
    """
    inc = IncidentService.get_incident(db, incident_id)
    if not inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found.",
        )
    return inc


@router.patch("/incidents/{incident_id}", response_model=IncidentResponse)
def update_incident(incident_id: str, update_data: IncidentUpdate, db: Session = Depends(get_db)):
    """
    Updates incident status, casualty counts, or user priority.
    """
    report = db.query(EmergencyReport).filter(EmergencyReport.id == incident_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found.",
        )

    if update_data.status:
        report.status = update_data.status
    if update_data.affected_people is not None:
        report.affected_people = update_data.affected_people
    if update_data.injuries is not None:
        report.injuries = update_data.injuries
    if update_data.description:
        report.description = update_data.description

    db.commit()
    db.refresh(report)
    return IncidentService._to_response(report)
