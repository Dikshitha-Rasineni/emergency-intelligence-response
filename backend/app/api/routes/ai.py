import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import AIExtraction, EmergencyReport

from genai.extractor import (
    detect_missing_information,
    extract_emergency_information,
    understand_multilingual_emergency,
)

from genai.safety import generate_safety_precautions
from genai.guidance import generate_reporter_guidance

from genai.response import (
    generate_response_recommendation,
    generate_incident_report,
)


router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


# ============================================================
# AI EXTRACTION
# ============================================================

class AIExtractionRequest(BaseModel):
    incident_id: str = Field(..., min_length=1)


class AIExtractionResponse(BaseModel):
    extraction_id: str
    incident_id: str
    emergency_type: str
    affected_people: int
    injuries: int
    critical_indicators: list[str]
    location_information: str


# ============================================================
# MISSING INFORMATION
# ============================================================

class MissingInformationRequest(BaseModel):
    incident_id: str = Field(..., min_length=1)


class MissingInformationResponse(BaseModel):
    incident_id: str
    known_information: list[str]
    missing_information: list[str]
    urgency: str


# ============================================================
# MULTILINGUAL
# ============================================================

class MultilingualEmergencyRequest(BaseModel):
    description: str = Field(
        ...,
        min_length=5,
    )


class MultilingualEmergencyResponse(BaseModel):
    detected_language: str
    normalized_report: str
    emergency_type: str
    affected_people: int
    injuries: int
    critical_indicators: list[str]
    location_information: str


# ============================================================
# SAFETY PRECAUTIONS
# ============================================================

class SafetyPrecautionRequest(BaseModel):
    incident_id: str = Field(..., min_length=1)


class SafetyPrecautionResponse(BaseModel):
    incident_id: str
    emergency_type: str
    critical_indicators: list[str]
    precautions: list[str]
    avoid_actions: list[str]


# ============================================================
# REPORTER GUIDANCE
# ============================================================

class ReporterGuidanceRequest(BaseModel):
    incident_id: str


class ReporterGuidanceResponse(BaseModel):
    incident_id: str
    emergency_type: str
    critical_indicators: list[str]
    guidance: list[str]
    emergency_contact: str


# ============================================================
# 3.6 - RESPONSE GENERATION
# ============================================================

class ResponseRecommendationRequest(BaseModel):
    incident_id: str = Field(..., min_length=1)

    # Optional for now.
    # These will later come from the ML severity/priority module.
    severity: str | None = None
    priority: str | None = None

    # Optional for now.
    # These will later come from the resource-ranking module.
    ranked_resources: list[dict] = Field(
        default_factory=list
    )

    # Optional missing-information list.
    missing_information: list[str] = Field(
        default_factory=list
    )


class ResponseRecommendationResponse(BaseModel):
    incident_id: str
    emergency_type: str
    situation_summary: str
    recommended_response: list[str]
    resource_recommendation: list[str]
    severity: str
    priority: str
    reasoning: str
    information_gaps: list[str]

    # Multilingual output (present only for non-English reports).
    response_language: str | None = None
    localized: dict | None = None


# ============================================================
# 3.7 - INCIDENT REPORT GENERATION
# ============================================================

class IncidentReportRequest(BaseModel):
    incident_id: str = Field(..., min_length=1)

    # Optional for now.
    severity: str | None = None
    priority: str | None = None

    # Optional for now.
    ranked_resources: list[dict] = Field(
        default_factory=list
    )

    # Optional missing-information list.
    missing_information: list[str] = Field(
        default_factory=list
    )


class IncidentReportResponse(BaseModel):
    incident_id: str
    incident_summary: str
    emergency_type: str
    location: str
    affected_people: int
    injuries: int
    critical_indicators: list[str]
    severity: str
    priority: str
    resources: list[dict]
    response_recommendation: list[str]
    information_gaps: list[str]
    report_summary: str

    # Multilingual output (present only for non-English reports).
    response_language: str | None = None
    localized: dict | None = None


# ============================================================
# 1. EMERGENCY EXTRACTION
# ============================================================

@router.post(
    "/extract",
    response_model=AIExtractionResponse,
)
async def extract_emergency(
    request: AIExtractionRequest,
    db: Session = Depends(get_db),
):

    # 1. Find the incident
    incident = (
        db.query(EmergencyReport)
        .filter(
            EmergencyReport.id == request.incident_id
        )
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail=f"Incident '{request.incident_id}' not found.",
        )

    # 2. Run GenAI extraction
    try:
        result = extract_emergency_information(
            incident.description
        )

        # Preserve structured information already supplied
        # by the emergency report.
        result["affected_people"] = (
            incident.affected_people
        )

        result["injuries"] = incident.injuries

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"GenAI extraction failed: {str(exc)}",
        ) from exc

    # 3. Convert critical indicators list to JSON text
    critical_indicators_json = json.dumps(
        result["critical_indicators"]
    )

    # 4. Save extraction to PostgreSQL
    extraction = AIExtraction(
        incident_id=incident.id,
        emergency_type=result["emergency_type"],
        affected_people=result["affected_people"],
        injuries=result["injuries"],
        critical_indicators=critical_indicators_json,
        location_information=result[
            "location_information"
        ],
    )

    db.add(extraction)
    db.commit()
    db.refresh(extraction)

    # 5. Return structured response
    return AIExtractionResponse(
        extraction_id=extraction.id,
        incident_id=extraction.incident_id,
        emergency_type=extraction.emergency_type,
        affected_people=extraction.affected_people,
        injuries=extraction.injuries,
        critical_indicators=result[
            "critical_indicators"
        ],
        location_information=(
            extraction.location_information or ""
        ),
    )


# ============================================================
# 2. MISSING INFORMATION
# ============================================================

@router.post(
    "/missing-info",
    response_model=MissingInformationResponse,
)
async def missing_information(
    request: MissingInformationRequest,
    db: Session = Depends(get_db),
):

    # 1. Find the incident
    incident = (
        db.query(EmergencyReport)
        .filter(
            EmergencyReport.id == request.incident_id
        )
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail=f"Incident '{request.incident_id}' not found.",
        )

    try:
        # 2. Get the existing GenAI extraction
        extraction = extract_emergency_information(
            incident.description
        )

        # Preserve structured incident values
        extraction["affected_people"] = (
            incident.affected_people
        )

        extraction["injuries"] = incident.injuries

        # 3. Detect genuinely missing information
        result = detect_missing_information(
            description=incident.description,
            affected_people=incident.affected_people,
            injuries=incident.injuries,
            emergency_type=extraction["emergency_type"],
            location=incident.location,
            latitude=incident.latitude,
            longitude=incident.longitude,
            critical_indicators=extraction[
                "critical_indicators"
            ],
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Missing information detection failed: "
                f"{str(exc)}"
            ),
        ) from exc

    # 4. Return result
    return MissingInformationResponse(
        incident_id=incident.id,
        known_information=result[
            "known_information"
        ],
        missing_information=result[
            "missing_information"
        ],
        urgency=result["urgency"],
    )


# ============================================================
# 3. MULTILINGUAL EMERGENCY UNDERSTANDING
# ============================================================

@router.post(
    "/multilingual",
    response_model=MultilingualEmergencyResponse,
)
async def multilingual_emergency(
    request: MultilingualEmergencyRequest,
):

    try:
        result = extract_emergency_information(
            request.description
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Multilingual emergency understanding failed: "
                f"{str(exc)}"
            ),
        ) from exc

    return MultilingualEmergencyResponse(
        detected_language=result.get(
            "source_language",
            "Unknown",
        ),
        normalized_report=result.get(
            "translated_text",
            request.description,
        ),
        emergency_type=result["emergency_type"],
        affected_people=result["affected_people"],
        injuries=result["injuries"],
        critical_indicators=result[
            "critical_indicators"
        ],
        location_information=result[
            "location_information"
        ],
    )


# ============================================================
# 4. SAFETY PRECAUTIONS
# ============================================================

@router.post(
    "/safety",
    response_model=SafetyPrecautionResponse,
)
async def safety_precautions(
    request: SafetyPrecautionRequest,
    db: Session = Depends(get_db),
):

    # 1. Find the incident
    incident = (
        db.query(EmergencyReport)
        .filter(
            EmergencyReport.id == request.incident_id
        )
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail=f"Incident '{request.incident_id}' not found.",
        )

    try:
        # 2. Understand the incident
        extraction = extract_emergency_information(
            incident.description
        )

        # Preserve structured incident values
        extraction["affected_people"] = (
            incident.affected_people
        )

        extraction["injuries"] = incident.injuries

        # 3. Generate grounded safety guidance
        result = generate_safety_precautions(
            emergency_type=extraction["emergency_type"],
            critical_indicators=extraction[
                "critical_indicators"
            ],
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Safety precaution generation failed: "
                f"{str(exc)}"
            ),
        ) from exc

    # 4. Return controlled safety guidance
    return SafetyPrecautionResponse(
        incident_id=incident.id,
        emergency_type=result["emergency_type"],
        critical_indicators=extraction[
            "critical_indicators"
        ],
        precautions=result["precautions"],
        avoid_actions=result["avoid_actions"],
    )


# ============================================================
# 5. IMMEDIATE REPORTER GUIDANCE
# ============================================================

@router.post(
    "/reporter-guidance",
    response_model=ReporterGuidanceResponse,
)
def reporter_guidance(
    request: ReporterGuidanceRequest,
    db: Session = Depends(get_db),
):

    # 1. Find the incident
    incident = (
        db.query(EmergencyReport)
        .filter(
            EmergencyReport.id == request.incident_id
        )
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail=f"Incident '{request.incident_id}' not found.",
        )

    # 2. Understand the emergency description
    try:
        extraction = extract_emergency_information(
            incident.description
        )

        # EmergencyReport does not contain emergency_type.
        # Get it from GenAI extraction.
        emergency_type = extraction.get(
            "emergency_type",
            "other",
        )

        critical_indicators = extraction.get(
            "critical_indicators",
            [],
        )

        # 3. Generate controlled reporter guidance
        result = generate_reporter_guidance(
            emergency_type=emergency_type,
            critical_indicators=critical_indicators,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Reporter guidance generation failed: "
                f"{str(exc)}"
            ),
        ) from exc

    # 4. Return the guidance
    return ReporterGuidanceResponse(
        incident_id=incident.id,
        emergency_type=result["emergency_type"],
        critical_indicators=critical_indicators,
        guidance=result["guidance"],
        emergency_contact=result["emergency_contact"],
    )


# ============================================================
# 6. 3.6 - GENAI RESPONSE GENERATION
# ============================================================

@router.post(
    "/response",
    response_model=ResponseRecommendationResponse,
    # Omit null multilingual keys so English payloads are unchanged.
    response_model_exclude_none=True,
)
def response_recommendation(
    request: ResponseRecommendationRequest,
    db: Session = Depends(get_db),
):

    # 1. Find incident
    incident = (
        db.query(EmergencyReport)
        .filter(
            EmergencyReport.id == request.incident_id
        )
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail=f"Incident '{request.incident_id}' not found.",
        )

    try:
        # 2. Extract verified emergency information
        extraction = extract_emergency_information(
            incident.description
        )

        emergency_type = extraction.get(
            "emergency_type",
            "other",
        )

        critical_indicators = extraction.get(
            "critical_indicators",
            [],
        )

        # Multilingual: extraction has already detected the
        # reporter's language and translated the report to English.
        # Reuse both so the translator is not called a second time.
        # For English reports these are identical to the original
        # description and "English", so behavior is unchanged.
        english_description = (
            extraction.get("translated_text")
            or incident.description
        )

        source_language = extraction.get(
            "source_language",
            "English",
        )

        # Preserve structured incident values
        affected_people = incident.affected_people
        injuries = incident.injuries

        # 3. Generate response recommendation
        result = generate_response_recommendation(
            incident_description=english_description,
            emergency_type=emergency_type,
            affected_people=affected_people,
            injuries=injuries,
            critical_indicators=critical_indicators,
            location=incident.location,
            severity=request.severity,
            priority=request.priority,
            ranked_resources=request.ranked_resources,
            missing_information=request.missing_information,
            output_language=source_language,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Response recommendation generation failed: "
                f"{str(exc)}"
            ),
        ) from exc

    # 4. Return response recommendation
    return ResponseRecommendationResponse(
        incident_id=incident.id,
        emergency_type=emergency_type,
        situation_summary=result[
            "situation_summary"
        ],
        recommended_response=result[
            "recommended_response"
        ],
        resource_recommendation=result[
            "resource_recommendation"
        ],
        severity=result["severity"],
        priority=result["priority"],
        reasoning=result["reasoning"],
        information_gaps=result[
            "information_gaps"
        ],
        response_language=result.get(
            "response_language"
        ),
        localized=result.get("localized"),
    )


# ============================================================
# 7. 3.7 - INCIDENT REPORT GENERATION
# ============================================================

@router.post(
    "/incident-report",
    response_model=IncidentReportResponse,
    # Omit null multilingual keys so English payloads are unchanged.
    response_model_exclude_none=True,
)
def incident_report(
    request: IncidentReportRequest,
    db: Session = Depends(get_db),
):

    # 1. Find incident
    incident = (
        db.query(EmergencyReport)
        .filter(
            EmergencyReport.id == request.incident_id
        )
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail=f"Incident '{request.incident_id}' not found.",
        )

    try:
        # 2. Extract verified emergency information
        extraction = extract_emergency_information(
            incident.description
        )

        emergency_type = extraction.get(
            "emergency_type",
            "other",
        )

        critical_indicators = extraction.get(
            "critical_indicators",
            [],
        )

        # Multilingual: reuse the language and English translation
        # already produced by extraction (see /response above).
        english_description = (
            extraction.get("translated_text")
            or incident.description
        )

        source_language = extraction.get(
            "source_language",
            "English",
        )

        affected_people = incident.affected_people
        injuries = incident.injuries

        # 3. Generate response recommendation first.
        # Only its English text feeds the report, so localization
        # is skipped here (output_language="English") to avoid
        # translating text that is never returned.
        response_result = generate_response_recommendation(
            incident_description=english_description,
            emergency_type=emergency_type,
            affected_people=affected_people,
            injuries=injuries,
            critical_indicators=critical_indicators,
            location=incident.location,
            severity=request.severity,
            priority=request.priority,
            ranked_resources=request.ranked_resources,
            missing_information=request.missing_information,
            output_language="English",
        )

        # 4. Generate structured incident report
        # (localized into the reporter's language when non-English)
        report_result = generate_incident_report(
            incident_description=english_description,
            emergency_type=emergency_type,
            affected_people=affected_people,
            injuries=injuries,
            critical_indicators=critical_indicators,
            location=incident.location,
            latitude=incident.latitude,
            longitude=incident.longitude,
            severity=request.severity,
            priority=request.priority,
            ranked_resources=request.ranked_resources,
            response_recommendation=response_result,
            missing_information=request.missing_information,
            output_language=source_language,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Incident report generation failed: "
                f"{str(exc)}"
            ),
        ) from exc

    # 5. Return structured incident report
    return IncidentReportResponse(
        incident_id=incident.id,
        incident_summary=report_result[
            "incident_summary"
        ],
        emergency_type=report_result[
            "emergency_type"
        ],
        location=report_result["location"],
        affected_people=report_result[
            "affected_people"
        ],
        injuries=report_result[
            "injuries"
        ],
        critical_indicators=report_result[
            "critical_indicators"
        ],
        severity=report_result[
            "severity"
        ],
        priority=report_result[
            "priority"
        ],
        resources=report_result[
            "resources"
        ],
        response_recommendation=report_result[
            "response_recommendation"
        ],
        information_gaps=report_result[
            "information_gaps"
        ],
        report_summary=report_result[
            "report_summary"
        ],
        response_language=report_result.get(
            "response_language"
        ),
        localized=report_result.get("localized"),
    )