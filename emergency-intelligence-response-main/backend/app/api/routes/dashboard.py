from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.incident import EmergencyReport
from app.models.severity_assessment import SeverityAssessment
from app.models.resource import EmergencyResource, ResourceAvailability
from app.schemas.dashboard import DashboardOverview
from app.services.incident_service import IncidentService
from app.services.resource_service import ResourceService

router = APIRouter()


@router.get("/dashboard/overview", response_model=DashboardOverview)
def get_dashboard_overview(db: Session = Depends(get_db)):
    """
    Returns multi-agency CAD operational dashboard overview.
    """
    total_active = db.query(EmergencyReport).filter(EmergencyReport.status != "RESOLVED").count()
    
    # Critical incidents
    critical_count = (
        db.query(SeverityAssessment)
        .join(EmergencyReport, SeverityAssessment.incident_id == EmergencyReport.id)
        .filter(EmergencyReport.status != "RESOLVED", SeverityAssessment.severity == "CRITICAL")
        .count()
    )

    # Available resources
    avail_resources_count = db.query(ResourceAvailability).filter(ResourceAvailability.status == "AVAILABLE").count()
    total_resources = db.query(EmergencyResource).count()
    readiness = round((avail_resources_count / max(1, total_resources)) * 100.0, 1)

    recent_incidents = IncidentService.list_incidents(db, limit=10)
    all_resources = ResourceService.get_nearby_resources(db, latitude=12.9716, longitude=77.5946, max_radius_km=50.0)

    return DashboardOverview(
        total_active_incidents=total_active,
        critical_incidents_count=critical_count,
        available_resources_count=avail_resources_count,
        system_readiness_pct=readiness,
        cad_status="OPERATIONAL",
        active_incidents=recent_incidents,
        resources=all_resources,
        system_telemetry={
            "database": "PostgreSQL 17 Live",
            "routing_engine": "GIS Road-Tortuosity Matrix Active",
            "ai_engine": "Ollama / Qwen / Local Fast-Parser Hybrid",
            "iot_broker": "HTTP / ESP32 Sensor Gateways Listening",
        },
    )


@router.get("/dashboard/incidents")
def get_dashboard_incidents(limit: int = 20, db: Session = Depends(get_db)):
    return IncidentService.list_incidents(db, limit=limit)


@router.get("/dashboard/resources")
def get_dashboard_resources(db: Session = Depends(get_db)):
    return ResourceService.get_nearby_resources(db, latitude=12.9716, longitude=77.5946, max_radius_km=50.0)
