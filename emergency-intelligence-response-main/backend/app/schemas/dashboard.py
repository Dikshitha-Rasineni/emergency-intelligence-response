from pydantic import BaseModel
from typing import List, Dict, Any
from app.schemas.incident import IncidentResponse
from app.schemas.resource import ResourceResponse


class DashboardOverview(BaseModel):
    total_active_incidents: int
    critical_incidents_count: int
    available_resources_count: int
    system_readiness_pct: float
    cad_status: str
    active_incidents: List[IncidentResponse]
    resources: List[ResourceResponse]
    system_telemetry: Dict[str, Any]
