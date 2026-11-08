from fastapi import APIRouter, Request
from app.core.rate_limit import check_rate
from app.schemas.ai import (
    AIExtractRequest,
    AIExtractResponse,
    PrecautionRequest,
    PrecautionResponse,
    RoleIntelligenceRequest,
    RoleIntelligenceResponse,
)
from app.services.ai_service import AIService

router = APIRouter()


@router.post("/ai/extract", response_model=AIExtractResponse)
def extract_incident_features(request: AIExtractRequest, req: Request):
    """Structured extraction (LLM if configured, otherwise rule-based). Rate limited."""
    check_rate(req, "ai", 20)
    return AIService.extract_incident_data(
        request.description,
        location_hint=request.location_hint,
        lang=request.language,
    )


@router.post("/ai/precautions", response_model=PrecautionResponse)
def generate_precautions(request: PrecautionRequest):
    """
    Generates non-diagnostic citizen precautions tailored to the emergency type.
    """
    return AIService.generate_precautions(
        emergency_type=request.emergency_type,
        description=request.description or "",
        priority=request.priority_score or 50,
        lang=request.language,
    )


@router.post("/ai/response", response_model=RoleIntelligenceResponse)
def generate_role_intelligence(request: RoleIntelligenceRequest):
    """
    Generates tactical decision support for Hospital, Police, or Fire responders.
    """
    return AIService.generate_role_intelligence(
        role=request.role,
        emergency_type=request.emergency_type,
        description=request.description,
        affected_people=request.affected_people,
        injuries=request.injuries,
        critical_indicators=request.critical_indicators,
        priority_score=request.priority_score,
        lang=request.language,
    )
