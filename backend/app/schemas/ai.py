from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class AIExtractRequest(BaseModel):
    description: str = Field(..., min_length=3, max_length=4000)
    location_hint: Optional[str] = None
    language: Optional[str] = None


class AIExtractResponse(BaseModel):
    emergency_type: str
    category: str
    affected_people: int
    injuries: int
    injury_certainty: str
    critical_indicators: List[str]
    hazards: List[str] = Field(default_factory=list)
    needs: List[str] = Field(default_factory=list)
    location_information: Optional[str] = None
    # Not calibrated: rule-based and LLM outputs carry no probability. Kept for API compatibility.
    confidence_score: Optional[float] = None
    missing_information: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    english_summary: Optional[str] = None
    method: str = "rule_based"
    model: Optional[str] = None
    latency_ms: Optional[int] = None
    language: Optional[str] = "en"


class PrecautionRequest(BaseModel):
    emergency_type: str
    description: Optional[str] = None
    priority_score: Optional[int] = None
    language: Optional[str] = None


class PrecautionResponse(BaseModel):
    emergency_type: str
    category: str
    precautions: List[str]
    disclaimer: str
    language: Optional[str] = "en"
    language_fallback: bool = False
    source: Dict[str, Any] = Field(default_factory=dict)


class RoleIntelligenceRequest(BaseModel):
    role: str  # HOSPITAL, POLICE, FIRE, DISASTER
    incident_id: Optional[str] = None
    emergency_type: str
    description: str
    affected_people: int = 0
    injuries: int = 0
    critical_indicators: List[str] = Field(default_factory=list)
    priority_score: int = 50
    language: Optional[str] = None


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
    suggestion_notice: str = "AI/rule-generated suggestions for trained personnel. Not a dispatch order."
    language: Optional[str] = "en"
