from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class AIExtractRequest(BaseModel):
    description: str = Field(..., min_length=5)
    location_hint: Optional[str] = None


class AIExtractResponse(BaseModel):
    emergency_type: str
    affected_people: int
    injuries: int
    critical_indicators: List[str]
    location_information: Optional[str] = None
    confidence_score: float = 0.95
    missing_information: List[str] = Field(default_factory=list)


class PrecautionRequest(BaseModel):
    emergency_type: str
    description: Optional[str] = None
    priority_score: Optional[int] = None


class PrecautionResponse(BaseModel):
    emergency_type: str
    precautions: List[str]
    disclaimer: str = "AI Recommended Precautions — public safety guidelines only. Not a medical diagnosis."


class RoleIntelligenceRequest(BaseModel):
    role: str  # HOSPITAL, POLICE, FIRE
    incident_id: Optional[str] = None
    emergency_type: str
    description: str
    affected_people: int
    injuries: int
    critical_indicators: List[str]
    priority_score: int


class RoleIntelligenceResponse(BaseModel):
    role: str
    summary: str
    recommendation: str
    operational_checklist: List[str]
    required_services: List[str]
    required_equipment: List[str]
    missing_information: List[str]
    traffic_impact: Optional[str] = None
    casualty_staging: Optional[str] = None
    tactical_deployments: Optional[str] = None
