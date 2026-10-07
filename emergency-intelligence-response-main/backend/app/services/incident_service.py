import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.incident import EmergencyReport
from app.models.ai_extraction import AIExtraction
from app.models.severity_assessment import SeverityAssessment
from app.models.recommendation import ResponseRecommendation
from app.models.resource import IncidentResource
from app.schemas.incident import IncidentCreate, IncidentResponse
from app.services.ai_service import AIService
from app.services.priority_service import PriorityService
from app.services.resource_service import ResourceService


class IncidentService:
    @staticmethod
    def _to_response(report: EmergencyReport) -> IncidentResponse:
        # Extract associated records if present
        ext = report.ai_extractions[0] if report.ai_extractions else None
        ass = report.severity_assessments[0] if report.severity_assessments else None
        rec = report.recommendations[0] if report.recommendations else None

        emergency_type = ext.emergency_type if ext else "General Emergency"
        critical_indicators = ext.critical_indicators if ext else []
        priority_score = int(ass.priority_score) if ass else 50
        severity = ass.severity if ass else "HIGH"

        precautions = rec.precautions if rec else []
        rec_data = {
            "summary": rec.summary if rec else "",
            "recommendation": rec.recommendation if rec else "",
            "operational_checklist": rec.operational_checklist if rec else [],
            "missing_information": rec.missing_information if rec else [],
        } if rec else None

        location_name = report.location or f"{round(report.latitude, 4)}° N, {round(report.longitude, 4)}° E"

        return IncidentResponse(
            incident_id=report.id,
            id=report.id,
            description=report.description,
            latitude=report.latitude,
            longitude=report.longitude,
            location_name=location_name,
            location=report.location,
            affected_people=report.affected_people,
            injuries=report.injuries,
            critical_indicators=critical_indicators,
            emergency_type=emergency_type,
            priority_score=priority_score,
            system_priority=priority_score,
            user_priority=priority_score,
            severity=severity,
            status=report.status,
            source=report.source,
            created_at=report.created_at,
            updated_at=report.updated_at,
            precautions=precautions,
            recommendations=rec_data,
        )

    @classmethod
    def create_incident(cls, db: Session, data: IncidentCreate) -> IncidentResponse:
        # 1. AI Extraction
        extraction = AIService.extract_incident_data(
            data.description,
            location_hint=data.location_name or data.location
        )

        emergency_type = data.emergency_type or extraction.emergency_type
        affected = max(data.affected_people, extraction.affected_people)
        injuries = max(data.injuries, extraction.injuries)
        indicators = list(set((data.critical_indicators or []) + extraction.critical_indicators))
        loc_str = data.location_name or data.location or extraction.location_information

        # 2. Priority & Severity Engine
        score, severity, factors = PriorityService.calculate_priority(
            description=data.description,
            injuries=injuries,
            affected_people=affected,
            critical_indicators=indicators,
            emergency_type=emergency_type,
        )

        # 3. Create EmergencyReport record
        inc_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        report = EmergencyReport(
            id=inc_id,
            description=data.description,
            latitude=data.latitude,
            longitude=data.longitude,
            location=loc_str,
            affected_people=affected,
            injuries=injuries,
            status="REPORTED",
            source=data.source,
        )
        db.add(report)
        db.flush()

        # 4. Save AI Extraction
        ai_record = AIExtraction(
            incident_id=report.id,
            emergency_type=emergency_type,
            affected_people=affected,
            injuries=injuries,
            critical_indicators=indicators,
            location_information=loc_str,
            raw_response=None,
        )
        db.add(ai_record)

        # 5. Save Severity Assessment
        ass_record = SeverityAssessment(
            incident_id=report.id,
            severity=severity,
            priority_score=float(score),
            factors=factors,
        )
        db.add(ass_record)

        # 6. Generate AI Precautions and Recommendations
        precautions_obj = AIService.generate_precautions(emergency_type, data.description, score)
        role_intel = AIService.generate_role_intelligence(
            role="ALL",
            emergency_type=emergency_type,
            description=data.description,
            affected_people=affected,
            injuries=injuries,
            critical_indicators=indicators,
            priority_score=score,
        )

        rec_record = ResponseRecommendation(
            incident_id=report.id,
            role="ALL",
            summary=role_intel.summary,
            recommendation=role_intel.recommendation,
            precautions=precautions_obj.precautions,
            operational_checklist=role_intel.operational_checklist,
            missing_information=extraction.missing_information,
        )
        db.add(rec_record)

        # 7. Discover and Associate Ranked Resources
        ranked_resources = ResourceService.rank_resources(
            db=db,
            latitude=report.latitude,
            longitude=report.longitude,
            emergency_type=emergency_type,
            injuries=injuries,
            affected_people=affected,
        )

        for res in ranked_resources[:5]:
            inc_res = IncidentResource(
                incident_id=report.id,
                resource_id=res.id,
                distance=res.distance_km or 0.0,
                suitability_score=res.suitability_score or 50.0,
                ranking=res.ranking or 1,
            )
            db.add(inc_res)

        db.commit()
        db.refresh(report)
        return cls._to_response(report)

    @classmethod
    def get_incident(cls, db: Session, incident_id: str) -> Optional[IncidentResponse]:
        report = db.query(EmergencyReport).filter(EmergencyReport.id == incident_id).first()
        if not report:
            return None
        return cls._to_response(report)

    @classmethod
    def list_incidents(cls, db: Session, limit: int = 50) -> List[IncidentResponse]:
        reports = db.query(EmergencyReport).order_by(EmergencyReport.created_at.desc()).limit(limit).all()
        return [cls._to_response(r) for r in reports]
