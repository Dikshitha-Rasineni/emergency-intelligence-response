import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.incident import EmergencyReport
from app.models.ai_extraction import AIExtraction
from app.models.severity_assessment import SeverityAssessment
from app.models.recommendation import ResponseRecommendation
from app.models.resource import IncidentResource
from app.schemas.incident import IncidentCreate, IncidentUpdate, IncidentResponse
from app.services.ai_service import AIService
from app.services.priority_service import PriorityService
from app.services.resource_service import ResourceService
from app.services.language_service import LanguageService
from app.services.geospatial_discovery_service import GeospatialDiscoveryService


class IncidentService:
    @staticmethod
    def _to_response(report: EmergencyReport) -> IncidentResponse:
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

        # Exact user-entered location retained; never overwritten with hardcoded default
        if report.location:
            loc_name = report.location
        elif report.latitude is not None and report.longitude is not None:
            loc_name = f"{round(report.latitude, 4)}° N, {round(report.longitude, 4)}° E"
        else:
            loc_name = "Location Unspecified"
        loc_source = getattr(report, "location_source", "USER_ENTERED") or "USER_ENTERED"
        coords_verified = getattr(report, "coordinates_verified", True)
        if coords_verified is None:
            coords_verified = True
        detected_lang = getattr(report, "detected_language", "en") or "en"

        return IncidentResponse(
            incident_id=report.id,
            id=report.id,
            description=report.description,
            latitude=report.latitude,
            longitude=report.longitude,
            location_name=loc_name,
            location=report.location,
            location_source=loc_source,
            coordinates_verified=coords_verified,
            detected_language=detected_lang,
            language=detected_lang,
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
        user_loc = data.location_name or data.location
        detected_lang = data.language or LanguageService.detect_language(data.description)

        # 1. Location and Coordinate Resolution
        lat = data.latitude
        lng = data.longitude
        loc_source = "USER_ENTERED"
        coords_verified = True

        if lat is not None and lng is not None and not (lat == 0.0 and lng == 0.0):
            loc_source = "DEVICE_GPS" if (data.source == "USER" and lat and lng) else "USER_COORDINATES"
            coords_verified = True
        elif user_loc and user_loc.strip():
            # Attempt geocoding of the user-entered location text
            geocoded = GeospatialDiscoveryService.geocode_location(user_loc)
            if geocoded:
                lat, lng, _ = geocoded
                loc_source = "GEOCODED"
                coords_verified = True
            else:
                # Retain the exact user-provided text, mark as unverified without silently injecting hardcoded coordinates
                lat = None
                lng = None
                loc_source = "UNVERIFIED"
                coords_verified = False
        else:
            user_loc = "Location Unspecified"
            lat = None
            lng = None
            loc_source = "UNVERIFIED"
            coords_verified = False

        # 2. AI Extraction with language support
        extraction = AIService.extract_incident_data(
            data.description,
            location_hint=user_loc,
            lang=detected_lang,
        )

        emergency_type = data.emergency_type or extraction.emergency_type
        affected = max(data.affected_people, extraction.affected_people)
        injuries = max(data.injuries, extraction.injuries)
        indicators = list(set((data.critical_indicators or []) + extraction.critical_indicators))

        # 3. Priority & Severity Engine
        score, severity, factors = PriorityService.calculate_priority(
            description=data.description,
            injuries=injuries,
            affected_people=affected,
            critical_indicators=indicators,
            emergency_type=emergency_type,
        )

        # 4. Create EmergencyReport record
        inc_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        report = EmergencyReport(
            id=inc_id,
            description=data.description,
            latitude=lat,
            longitude=lng,
            location=user_loc,
            location_source=loc_source,
            coordinates_verified=coords_verified,
            detected_language=detected_lang,
            affected_people=affected,
            injuries=injuries,
            status="REPORTED",
            source=data.source,
        )
        db.add(report)
        db.flush()

        # 5. Save AI Extraction
        ai_record = AIExtraction(
            incident_id=report.id,
            emergency_type=emergency_type,
            affected_people=affected,
            injuries=injuries,
            critical_indicators=indicators,
            location_information=user_loc,
            raw_response=None,
        )
        db.add(ai_record)

        # 6. Save Severity Assessment
        ass_record = SeverityAssessment(
            incident_id=report.id,
            severity=severity,
            priority_score=float(score),
            factors=factors,
        )
        db.add(ass_record)

        # 7. Generate Multilingual Precautions and Recommendations
        precautions_obj = AIService.generate_precautions(
            emergency_type=emergency_type,
            description=data.description,
            priority=score,
            lang=detected_lang,
        )
        role_intel = AIService.generate_role_intelligence(
            role="ALL",
            emergency_type=emergency_type,
            description=data.description,
            affected_people=affected,
            injuries=injuries,
            critical_indicators=indicators,
            priority_score=score,
            lang=detected_lang,
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

        # 8. Discover and Associate Real Ranked Resources (if coordinates verified/available)
        if report.latitude is not None and report.longitude is not None:
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
    def update_incident(cls, db: Session, incident_id: str, update_data: IncidentUpdate) -> Optional[IncidentResponse]:
        report = db.query(EmergencyReport).filter(EmergencyReport.id == incident_id).first()
        if not report:
            return None

        # 1. Update basic fields
        if update_data.status:
            report.status = update_data.status
        if update_data.affected_people is not None:
            report.affected_people = update_data.affected_people
        if update_data.injuries is not None:
            report.injuries = update_data.injuries
        if update_data.language:
            report.detected_language = update_data.language

        # 2. Location update logic:
        # If user explicitly changes location, update it; otherwise PRESERVE existing location
        new_loc = update_data.location_name or update_data.location
        if new_loc and new_loc.strip():
            report.location = new_loc.strip()
            if update_data.latitude is not None and update_data.longitude is not None:
                report.latitude = update_data.latitude
                report.longitude = update_data.longitude
                report.location_source = "DEVICE_GPS"
                report.coordinates_verified = True
            else:
                geocoded = GeospatialDiscoveryService.geocode_location(new_loc.strip())
                if geocoded:
                    report.latitude = geocoded[0]
                    report.longitude = geocoded[1]
                    report.location_source = "GEOCODED"
                    report.coordinates_verified = True
                else:
                    report.latitude = None
                    report.longitude = None
                    report.location_source = "UNVERIFIED"
                    report.coordinates_verified = False

        # 3. Description update: Re-run extraction and priority if description changes
        if update_data.description and update_data.description.strip():
            report.description = update_data.description.strip()
            if not update_data.language:
                report.detected_language = LanguageService.detect_language(report.description)

            extraction = AIService.extract_incident_data(
                report.description,
                location_hint=report.location,
                lang=report.detected_language,
            )
            score, severity, factors = PriorityService.calculate_priority(
                description=report.description,
                injuries=report.injuries,
                affected_people=report.affected_people,
                critical_indicators=extraction.critical_indicators,
                emergency_type=extraction.emergency_type,
            )

            if report.severity_assessments:
                ass = report.severity_assessments[0]
                ass.priority_score = float(score)
                ass.severity = severity
                ass.factors = factors

            precautions_obj = AIService.generate_precautions(
                emergency_type=extraction.emergency_type,
                description=report.description,
                priority=score,
                lang=report.detected_language,
            )
            role_intel = AIService.generate_role_intelligence(
                role="ALL",
                emergency_type=extraction.emergency_type,
                description=report.description,
                affected_people=report.affected_people,
                injuries=report.injuries,
                critical_indicators=extraction.critical_indicators,
                priority_score=score,
                lang=report.detected_language,
            )
            if report.recommendations:
                rec = report.recommendations[0]
                rec.summary = role_intel.summary
                rec.recommendation = role_intel.recommendation
                rec.precautions = precautions_obj.precautions
                rec.operational_checklist = role_intel.operational_checklist

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
