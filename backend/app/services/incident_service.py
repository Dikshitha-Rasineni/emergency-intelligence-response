"""
Canonical incident pipeline. Both citizen reports and IoT alerts converge here.

create (fast, synchronous; < ~100 ms without external calls)
  language detection -> location resolution -> rule-based extraction -> duplicate merge check
  -> persist -> assess (priority + department routing + notifications + guidance) -> commit
enrich (background)
  LLM extraction -> validated -> re-assess -> push updates
media (background)
  vision analysis -> re-assess

Re-assessment always recomputes from the stored evidence of the canonical incident and all
reports merged into it, so the citizen view and the control-room views are derived from
the same record and cannot contradict each other.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.core.security import new_tracking_token, hash_tracking_token
from app.models.ai_extraction import AIExtraction
from app.models.incident import EmergencyReport
from app.models.operations import RoutingDecision, IncidentUpdate
from app.models.recommendation import ResponseRecommendation
from app.models.resource import IncidentResource
from app.models.sensor import SensorReading, Device
from app.models.severity_assessment import SeverityAssessment
from app.services import department_routing_service as routing_policy
from app.services.ai_service import AIService, Extraction
from app.services.audit_service import AuditService
from app.services.dispatch_service import DispatchService
from app.services.geospatial_discovery_service import GeospatialDiscoveryService
from app.services.language_service import LanguageService
from app.services.notification_service import NotificationService
from app.services.priority_service import PriorityService
from app.services.rag_service import RagService
from app.services.realtime import manager
from app.services.resource_service import ResourceService, TYPES_FOR_CATEGORY
from app.services.taxonomy import normalize_category, label, guidance_for, SUPPORTED_UI_LANGUAGES
from app.services.vision_service import VisionService

OPEN_STATUSES = ("REPORTED", "ACKNOWLEDGED", "RESPONDING", "ON_SCENE")
COMPATIBLE = {"fire": {"fire", "gas_leak"}, "gas_leak": {"fire", "gas_leak"},
              "rescue": {"rescue", "structural_collapse"}, "structural_collapse": {"rescue", "structural_collapse"}}
DEPT_RESOURCE_TYPES = {"HOSPITAL": ("HOSPITAL", "AMBULANCE"), "POLICE": ("POLICE",), "FIRE": ("FIRE",),
                       "DISASTER": ("DISASTER", "SHELTER")}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return f"INC-{uuid.uuid4().hex[:8].upper()}"


class IncidentService:
    # =================================================================== intake
    @staticmethod
    def _resolve_location(lat, lng, text_loc: Optional[str], source_hint: Optional[str], accuracy: Optional[float]):
        if lat is not None and lng is not None and not (lat == 0.0 and lng == 0.0):
            src = (source_hint or "DEVICE_GPS").upper()
            if src not in ("DEVICE_GPS", "MANUAL_PIN", "DEVICE_REGISTERED", "IOT_EVENT"):
                src = "DEVICE_GPS"
            verified = src in ("DEVICE_GPS", "MANUAL_PIN", "DEVICE_REGISTERED") and (accuracy is None or accuracy <= 1000)
            return lat, lng, src, verified
        if text_loc and text_loc.strip():
            geo = GeospatialDiscoveryService.geocode_location(text_loc)
            if geo:
                return geo[0], geo[1], "GEOCODED", False  # approximate: geocoded from free text
        return None, None, "UNVERIFIED", False

    @staticmethod
    def _find_merge_target(db: Session, lat: Optional[float], lng: Optional[float], category: str,
                           exclude_id: Optional[str] = None) -> Optional[EmergencyReport]:
        if lat is None or lng is None or category in ("other", "sos"):
            return None
        since = _now() - timedelta(minutes=settings.IOT_MERGE_WINDOW_MIN)
        rows = db.execute(text("""
            SELECT id FROM emergency_reports
            WHERE merged_into_id IS NULL AND status = ANY(:open) AND created_at >= :since AND geom IS NOT NULL
              AND ST_DWithin(geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :r)
              AND (CAST(:ex AS text) IS NULL OR id <> CAST(:ex AS text))
            ORDER BY ST_Distance(geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) LIMIT 5
        """), {"open": list(OPEN_STATUSES), "since": since, "lat": lat, "lng": lng,
               "r": settings.IOT_MERGE_RADIUS_M, "ex": exclude_id}).all()
        compat = COMPATIBLE.get(category, {category})
        for (rid,) in rows:
            inc = db.get(EmergencyReport, rid)
            if inc and (inc.category in compat):
                return inc
        return None

    @staticmethod
    def _store_extraction(db: Session, incident_id: str, ex: Extraction) -> AIExtraction:
        rec = AIExtraction(
            incident_id=incident_id, emergency_type=ex.emergency_type, category=ex.category,
            affected_people=ex.affected_people, injuries=ex.injuries, critical_indicators=ex.critical_indicators,
            hazards=ex.hazards, needs=ex.needs,
            uncertainties=ex.uncertainties + ([f"injury_certainty:{ex.injury_certainty}"]),
            location_information=ex.location_text, english_summary=ex.english_summary, method=ex.method,
            model_name=ex.model, latency_ms=ex.latency_ms, validation_notes=ex.validation_notes,
            raw_response=ex.raw,
        )
        db.add(rec)
        db.flush()
        return rec

    @classmethod
    def create_citizen_report(cls, db: Session, data, actor_ip: Optional[str] = None) -> Tuple[EmergencyReport, str, Optional[EmergencyReport]]:
        """Returns (report_row, tracking_token, canonical_if_merged)."""
        lang_info = LanguageService.detect(data.description)
        detected = data.language if data.language and data.language != "auto" else lang_info["language"]
        preferred = data.preferred_language if data.preferred_language in SUPPORTED_UI_LANGUAGES else None
        text_loc = data.location_name or data.location
        lat, lng, loc_src, verified = cls._resolve_location(data.latitude, data.longitude, text_loc,
                                                            data.location_source, data.location_accuracy_m)
        ex = AIService.extract(data.description, detected, use_llm=False)
        user_cat = normalize_category(data.emergency_type) if data.emergency_type else None
        if user_cat and ex.category == "other":
            ex.category, ex.emergency_type = user_cat, label(user_cat)
        if data.injuries and data.injuries > ex.injuries:
            ex.injuries, ex.injury_certainty = data.injuries, "confirmed"
        ex.affected_people = max(ex.affected_people, data.affected_people or 0, ex.injuries)

        token = new_tracking_token()
        report = EmergencyReport(
            id=_new_id(), description=data.description, latitude=lat, longitude=lng,
            location=(text_loc or "").strip()[:255] or None, location_source=loc_src, coordinates_verified=verified,
            location_accuracy_m=data.location_accuracy_m, detected_language=detected,
            language_confidence=lang_info["confidence"], preferred_language=preferred, category=ex.category,
            user_selected_category=user_cat, affected_people=ex.affected_people, injuries=ex.injuries,
            status="REPORTED", source="USER", ai_status="PENDING", tracking_token_hash=hash_tracking_token(token),
        )
        db.add(report)
        db.flush()
        cls._store_extraction(db, report.id, ex)

        target = cls._find_merge_target(db, lat, lng, ex.category, exclude_id=report.id)
        if target:
            report.merged_into_id = target.id
            report.status = "MERGED"
            db.flush()
            db.add(IncidentUpdate(incident_id=target.id, actor_label="system", status=target.status, public=False,
                                  note=f"Linked citizen report {report.id} merged (same category within "
                                       f"{int(settings.IOT_MERGE_RADIUS_M)} m / {settings.IOT_MERGE_WINDOW_MIN} min)"))
        AuditService.record(db, "citizen", "incident.create", "incident", report.id,
                            {"merged_into": target.id if target else None, "lang": detected}, ip=actor_ip)
        canonical = target or report
        cls.assess(db, canonical)
        db.commit()
        db.refresh(report)
        cls.push_updates(db, canonical)
        return report, token, target

    @classmethod
    def create_from_iot(cls, db: Session, reading: SensorReading, category: str, device_label: str) -> Tuple[EmergencyReport, bool]:
        """Qualified IoT alert -> merge into a nearby open incident or create one. Returns (canonical, merged)."""
        target = cls._find_merge_target(db, reading.latitude, reading.longitude, category)
        if target:
            reading.incident_id = target.id
            db.add(IncidentUpdate(incident_id=target.id, actor_label=f"device:{reading.device_id}", public=False,
                                  note=f"Corroborating sensor alert {reading.reason or reading.event_type} attached"))
            db.flush()  # the reading must be linked before reassessment reads the incident's sensors
            cls.assess(db, target)
            return target, True
        unit = reading.measurement_unit or ""
        desc = (f"Automated sensor alert from {device_label}: {reading.reason or reading.event_type} "
                f"(sensor {reading.source_sensor or 'n/a'}, observed {reading.observed_value} {unit}, "
                f"threshold {reading.threshold_value} {unit}). Not yet confirmed by a person.")
        ex = Extraction(category=category, emergency_type=label(category), injury_certainty="unknown",
                        hazards={"fire": ["fire", "smoke"], "gas_leak": ["gas"], "flood": ["flood_water"],
                                 "road_accident": ["traffic"]}.get(category, []),
                        needs={"road_accident": ["traffic_control"], "fire": ["fire_suppression"],
                               "gas_leak": ["fire_suppression"]}.get(category, []),
                        english_summary=desc, uncertainties=["Sensor-only event: not confirmed by a person",
                                                             "Number of people involved unknown"],
                        method="rule_based")
        inc = EmergencyReport(id=_new_id(), description=desc, latitude=reading.latitude, longitude=reading.longitude,
                              location=device_label, location_source="DEVICE_REGISTERED", coordinates_verified=True,
                              detected_language="en", language_confidence=1.0, category=category, status="REPORTED",
                              source="IOT", ai_status="RULE_BASED")
        db.add(inc)
        db.flush()
        reading.incident_id = inc.id
        db.flush()
        cls._store_extraction(db, inc.id, ex)
        cls.assess(db, inc)
        return inc, False

    # =============================================================== assessment
    @staticmethod
    def _report_card(r: EmergencyReport) -> Dict[str, Any]:
        ext = r.ai_extractions[0] if r.ai_extractions else None
        lang = r.detected_language or "en"
        english = r.english_translation or (r.description if lang == "en" else (ext.english_summary if ext else None))
        return {"id": r.id, "created_at": r.created_at, "source": r.source, "language": lang,
                "original_text": r.description if r.source != "IOT" else None,
                "english_text": english,
                "english_kind": ("original" if lang == "en" else "machine_translation" if r.english_translation
                                 else "fact_summary" if english else "unavailable"),
                "translation_provider": r.translation_provider, "location_label": r.location}

    @staticmethod
    def sensor_is_severe(s: SensorReading) -> bool:
        sev = (s.hazard_severity or "").upper()
        ratio = (s.observed_value / s.threshold_value) if s.observed_value and s.threshold_value else 0
        return sev in ("HIGH", "CRITICAL") or (s.acceleration_magnitude_g or 0) >= 4.0 or ratio >= 1.5

    @staticmethod
    def _linked_reports(db: Session, canonical: EmergencyReport) -> List[EmergencyReport]:
        return [canonical] + db.query(EmergencyReport).filter(EmergencyReport.merged_into_id == canonical.id).all()

    @classmethod
    def combined_facts(cls, db: Session, inc: EmergencyReport) -> Dict[str, Any]:
        reports = cls._linked_reports(db, inc)
        exts = [r.ai_extractions[0] for r in reports if r.ai_extractions]
        injuries, certainty, affected = 0, "unknown", 0
        hazards, needs, indicators, uncertainties = set(), set(), [], []
        summaries = []
        rank = {"confirmed": 4, "possible": 3, "denied": 2, "none_reported": 1, "unknown": 0}
        cat = inc.category or "other"
        for e in exts:
            cert = next((u.split(":", 1)[1] for u in (e.uncertainties or []) if u.startswith("injury_certainty:")), "unknown")
            if e.injuries > injuries or (e.injuries == injuries and rank.get(cert, 0) > rank.get(certainty, 0)):
                injuries, certainty = e.injuries, cert
            affected = max(affected, e.affected_people)
            hazards |= set(e.hazards or [])
            needs |= set(e.needs or [])
            indicators += [i for i in (e.critical_indicators or []) if i not in indicators]
            uncertainties += [u for u in (e.uncertainties or []) if not u.startswith("injury_certainty:") and u not in uncertainties]
            if e.english_summary:
                summaries.append(e.english_summary)
        if exts:
            primary = exts[0] if exts[0].method == "llm" or len(exts) == 1 else exts[0]
            if primary.category and primary.category != "other":
                cat = primary.category
        media = [m for r in reports for m in r.media]
        sensors = db.query(SensorReading).filter(SensorReading.incident_id == inc.id,
                                                 SensorReading.alert_qualified.is_(True)).all()
        img_findings = VisionService.findings_for_assessment(media)
        return {
            "category": cat, "injuries": injuries, "injury_certainty": certainty, "affected_people": max(affected, injuries),
            "hazards": sorted(hazards), "needs": sorted(needs), "critical_indicators": indicators,
            "trapped": "Occupants trapped on scene" in indicators,
            "unconscious": "Unconscious casualty reported" in indicators,
            "uncertainties": uncertainties, "english_summary": summaries[0] if summaries else None,
            "linked_reports": reports, "media": media, "sensors": sensors, "image_findings": img_findings,
        }

    @classmethod
    def assess(cls, db: Session, inc: EmergencyReport, override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        f = cls.combined_facts(db, inc)
        sensor_ev = [{"device_id": s.device_id, "reason": s.reason, "event_type": s.event_type,
                      "severe": cls.sensor_is_severe(s)} for s in f["sensors"]]
        result = PriorityService.assess(
            category=f["category"], injuries=f["injuries"], injury_certainty=f["injury_certainty"],
            affected_people=f["affected_people"], hazards=f["hazards"], trapped=f["trapped"],
            unconscious=f["unconscious"], image_findings=f["image_findings"], sensor_events=sensor_ev,
            location_verified=bool(inc.coordinates_verified), extra_uncertainties=f["uncertainties"],
            report_source="sensor_event" if inc.source == "IOT" else "user_report",
        )
        prev = inc.severity_assessments[0] if inc.severity_assessments else None
        if override:
            score = int(override["score"])
            from app.services.priority_service import severity_for
            result.update(score=score, severity=severity_for(score))
        elif prev and prev.assessed_by != "system":
            # A human override stands until a human changes it; still record new evidence.
            result.update(score=int(prev.priority_score), severity=prev.severity)
        if not prev or override or prev.priority_score != result["score"] or prev.evidence != result["evidence"]:
            db.add(SeverityAssessment(
                incident_id=inc.id, severity=result["severity"], priority_score=float(result["score"]),
                factors=result["factors"], evidence=result["evidence"], uncertainties=result["uncertainties"],
                assessment_version=result["version"],
                assessed_by=override["user_id"] if override else (prev.assessed_by if prev and prev.assessed_by != "system" else "system"),
                override_reason=override.get("reason") if override else (prev.override_reason if prev and prev.assessed_by != "system" else None),
            ))
        inc.category = f["category"]
        inc.injuries, inc.affected_people = f["injuries"], f["affected_people"]

        # ---- department routing (deterministic)
        visual = {x["finding"] for x in f["image_findings"] if x.get("confidence_level") in ("high", "medium")}
        sensor_types = {s.event_type.upper() for s in f["sensors"]}
        sensor_severe = any(cls.sensor_is_severe(s) for s in f["sensors"])
        decisions = routing_policy.decide({
            "category": f["category"], "needs": f["needs"], "hazards": f["hazards"], "injuries": f["injuries"],
            "affected_people": f["affected_people"], "trapped": f["trapped"], "unconscious": f["unconscious"],
            "severity": result["severity"], "visual_findings": visual, "sensor_types": sensor_types,
            "sensor_severe": sensor_severe,
        })
        current = {d.department: d for d in inc.routing_decisions if not d.superseded}
        changed = False
        for d in decisions:
            cur = current.get(d["department"])
            if cur and cur.included == d["included"] and cur.role_in_response == d["role"] and cur.reasons == d["reasons"]:
                continue
            if cur:
                cur.superseded = True
            db.add(RoutingDecision(incident_id=inc.id, department=d["department"], included=d["included"],
                                   role_in_response=d["role"], reasons=d["reasons"],
                                   policy_version=routing_policy.POLICY_VERSION))
            changed = True
        db.flush()
        included = [d["department"] for d in decisions if d["included"]]
        excluded = [d["department"] for d in decisions if not d["included"]]
        if inc.status in OPEN_STATUSES:
            NotificationService.ensure_for_departments(db, inc.id, included, result["severity"])
            if changed:
                NotificationService.cancel_for_departments(db, inc.id, excluded, "no longer included by routing policy")

        # ---- associated resources (PostGIS nearest per relevant type)
        if inc.latitude is not None and inc.longitude is not None:
            wanted = set(TYPES_FOR_CATEGORY.get(f["category"], ()))
            for dep in included:
                wanted |= set(DEPT_RESOURCE_TYPES[dep])
            for old in list(inc.incident_resources):
                db.delete(old)
            rank = 1
            for t in sorted(wanted):
                for r in ResourceService.nearby_db(db, inc.latitude, inc.longitude, 25.0, [t], limit=3):
                    db.add(IncidentResource(incident_id=inc.id, resource_id=r.id, distance=r.distance_km or 0.0,
                                            suitability_score=0.0, ranking=rank))
                    rank += 1

        # ---- citizen guidance in their language (same canonical facts)
        lang = inc.preferred_language or inc.detected_language or "en"
        g = guidance_for(f["category"], lang)
        rec = next((r for r in inc.recommendations if r.role == "USER"), None)
        if not rec:
            rec = ResponseRecommendation(incident_id=inc.id, role="USER", summary="", recommendation="")
            db.add(rec)
        rec.language, rec.precautions, rec.precaution_sources = g["language"], g["items"], [g["source"]]
        rec.summary = label(f["category"])
        rec.recommendation = "language_fallback" if g["language_fallback"] else "ok"
        rec.missing_information = f["uncertainties"][:6]
        db.flush()
        db.expire(inc, ["severity_assessments", "routing_decisions", "incident_resources", "recommendations", "notifications"])
        # ---- automatic unit dispatch (sensor alerts, HIGH/CRITICAL) - nearest unit per primary department
        try:
            with db.begin_nested():  # a failure here must never undo the assessment above
                made = DispatchService.auto_dispatch(db, inc)
            if made:
                db.expire(inc, ["dispatches"])
        except Exception as e:
            logger.warning(f"auto-dispatch skipped for {inc.id}: {e}")
        return result

    # ============================================================== enrichment
    @classmethod
    def enrich_with_llm(cls, incident_id: str) -> None:
        """Background task (own DB session)."""
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            report = db.get(EmergencyReport, incident_id)
            if not report:
                return
            lang = report.detected_language or "en"
            canonical = db.get(EmergencyReport, report.merged_into_id) if report.merged_into_id else report
            # 1) Fast machine translation for control rooms (does not wait for the LLM)
            if lang != "en" and not report.english_translation:
                from app.services.translation_service import translate
                t, prov = translate(report.description, lang, "en")
                if t:
                    report.english_translation, report.translation_provider = t, prov
                    rule = AIService.extract(report.description, lang, use_llm=False, translation=t)
                    cls._store_extraction(db, report.id, rule)
                    cls.assess(db, canonical)
                    db.commit()
                    cls.push_updates(db, canonical)
            # 2) LLM extraction (may take a while on CPU); refines the facts when it succeeds
            ex = AIService.extract(report.description, lang, use_llm=True, translation=report.english_translation)
            if ex.method == "llm":
                if report.user_selected_category and ex.category == "other":
                    ex.category, ex.emergency_type = report.user_selected_category, label(report.user_selected_category)
                cls._store_extraction(db, report.id, ex)
                report.ai_status = "COMPLETED"
            else:
                report.ai_status = "RULE_BASED"
            if ex.method == "llm" and canonical.id == report.id:
                report.category = ex.category
            cls.assess(db, canonical)
            db.commit()
            cls.push_updates(db, canonical)
        except Exception as e:
            logger.exception(f"LLM enrichment failed for {incident_id}: {e}")
            db.rollback()
            try:
                r = db.get(EmergencyReport, incident_id)
                if r:
                    r.ai_status = "UNAVAILABLE"
                    db.commit()
            except Exception:
                db.rollback()
        finally:
            db.close()

    @classmethod
    def analyze_media(cls, media_id: str) -> None:
        from app.db.session import SessionLocal
        from app.models.media import IncidentMedia
        db = SessionLocal()
        try:
            m = db.get(IncidentMedia, media_id)
            if not m:
                return
            inc = db.get(EmergencyReport, m.incident_id)
            canonical = db.get(EmergencyReport, inc.merged_into_id) if inc.merged_into_id else inc
            VisionService.analyze(db, m, canonical.category or "other")
            db.commit()
            cls.assess(db, canonical)
            db.commit()
            cls.push_updates(db, canonical)
        except Exception as e:
            logger.exception(f"media analysis failed {media_id}: {e}")
            db.rollback()
            m = db.get(IncidentMedia, media_id)
            if m:
                m.status, m.analysis_error = "PROCESSING_FAILED", f"{type(e).__name__}"
                db.commit()
        finally:
            db.close()

    # =================================================================== views
    @classmethod
    def full_view(cls, db: Session, inc: EmergencyReport, with_route_for: Optional[str] = None) -> Dict[str, Any]:
        f = cls.combined_facts(db, inc)
        ass = inc.severity_assessments[0] if inc.severity_assessments else None
        ext = inc.ai_extractions[0] if inc.ai_extractions else None
        decisions = [d for d in inc.routing_decisions if not d.superseded]
        resources = []
        for ir in sorted(inc.incident_resources, key=lambda x: x.distance):
            r = ir.resource
            av = r.availability
            resources.append({"id": r.id, "name": r.name, "type": r.resource_type, "latitude": r.latitude,
                              "longitude": r.longitude, "address": r.address, "phone": r.phone if r.verified else None,
                              "straight_line_km": round(ir.distance, 2), "verified": r.verified,
                              "data_source": r.data_source,
                              "availability_status": av.status if av and av.verified else "UNKNOWN"})
        view = {
            "incident_id": inc.id, "category": f["category"], "emergency_type": label(f["category"]),
            "priority_score": int(ass.priority_score) if ass else None, "severity": ass.severity if ass else None,
            "priority_evidence": {"version": ass.assessment_version, "evidence": ass.evidence, "assessed_at": ass.created_at,
                                  "assessed_by": ass.assessed_by, "override_reason": ass.override_reason} if ass else None,
            "uncertainties": ass.uncertainties if ass else [],
            "status": inc.status, "source": inc.source, "created_at": inc.created_at, "updated_at": inc.updated_at,
            "location": {"label": inc.location or ("Device GPS location" if inc.latitude is not None else "Location not provided"), "latitude": inc.latitude, "longitude": inc.longitude,
                         "source": inc.location_source, "verified": bool(inc.coordinates_verified),
                         "accuracy_m": inc.location_accuracy_m},
            "english_summary": inc.english_translation or f["english_summary"] or (inc.description if (inc.detected_language or "en") == "en" else None),
            "translation": ({"text": inc.english_translation, "provider": inc.translation_provider,
                             "from_language": inc.detected_language} if inc.english_translation else None),
            "reports": [cls._report_card(r) for r in f["linked_reports"]],
            "original_text": inc.description, "original_language": inc.detected_language,
            "language_confidence": inc.language_confidence,
            "injuries": f["injuries"], "injury_certainty": f["injury_certainty"], "affected_people": f["affected_people"],
            "unconscious": f["unconscious"], "trapped": f["trapped"], "needs": f["needs"], "hazards": f["hazards"],
            "sensor_evidence": [{"device_id": s.device_id, "event_type": s.event_type, "reason": s.reason,
                                 "source_sensor": s.source_sensor, "observed_value": s.observed_value,
                                 "threshold_value": s.threshold_value, "unit": s.measurement_unit,
                                 "timestamp": s.timestamp, "event_id": s.event_id,
                                 "transport": s.transport, "signal_quality": s.signal_quality, "raw_adc": s.fsr_raw_adc,
                                 "sensor": s.source_sensor,
                                 "severity": s.hazard_severity, "severe": cls.sensor_is_severe(s),
                                 "device_name": (db.get(Device, s.device_id).name if db.get(Device, s.device_id) else s.device_id),
                                 "device_location": (db.get(Device, s.device_id).location_label if db.get(Device, s.device_id) else None)}
                                for s in f["sensors"]],
            "image_evidence": [VisionService.to_dict(m) for m in f["media"]],
            "resources": resources,
            "routing": [{"department": d.department, "included": d.included, "role": d.role_in_response,
                         "reasons": d.reasons, "policy_version": d.policy_version, "decided_at": d.created_at} for d in decisions],
            "notifications": [NotificationService.to_dict(n) for n in inc.notifications],
            "dispatches": [DispatchService.control_dict(db, d)
                           for d in DispatchService.active_and_recent(db, inc, refine=bool(with_route_for))],
            "dispatched_to": [{"department": d.department, "role": d.role_in_response,
                               "status": next((n.status for n in inc.notifications if n.department == d.department), None)}
                              for d in decisions if d.included],
            "linked_report_count": len(f["linked_reports"]) - 1,
            "linked_reports": [r.id for r in f["linked_reports"][1:]],
            "evidence_sources": sorted({"user_report" for r in f["linked_reports"] if r.source == "USER"}
                                       | ({"iot_sensor"} if f["sensors"] else set())
                                       | ({"image_analysis"} if f["image_findings"] else set())),
            "ai": {"status": inc.ai_status, "method": ext.method if ext else None, "model": ext.model_name if ext else None,
                   "latency_ms": ext.latency_ms if ext else None, "validation_notes": ext.validation_notes if ext else []},
            "updates": [{"at": u.created_at, "by": u.actor_label, "department": u.department, "status": u.status,
                         "note": u.note, "public": u.public} for u in inc.updates],
            "knowledge_excerpts": RagService.search(db, f["english_summary"] or "", f["category"], "en", limit=2),
        }
        if with_route_for and inc.latitude is not None:
            view["route"] = cls._route_for(view, with_route_for)
        return view

    _route_cache: Dict[Tuple[str, str], Tuple[float, Dict[str, Any]]] = {}

    @classmethod
    def _route_for(cls, view: Dict[str, Any], dept: str) -> Optional[Dict[str, Any]]:
        import time
        from app.services.routing_service import RoutingService
        types = DEPT_RESOURCE_TYPES.get(dept, ())
        cand = next((r for r in view["resources"] if r["type"] in types), None)
        if not cand:
            return {"available": False, "provider": "NONE", "message": "No registered resource of this department nearby"}
        key = (view["incident_id"], cand["id"])
        hit = cls._route_cache.get(key)
        if hit and time.time() - hit[0] < 300:
            return hit[1]
        r = RoutingService.calculate_route(cand["latitude"], cand["longitude"], view["location"]["latitude"],
                                           view["location"]["longitude"], origin_name=cand["name"],
                                           destination_name=view["location"]["label"])
        out = r.model_dump()
        out["resource_id"] = cand["id"]
        cls._route_cache[key] = (time.time(), out)
        return out

    @classmethod
    def department_view(cls, db: Session, inc: EmergencyReport, department: str, with_route: bool = False) -> Dict[str, Any]:
        full = cls.full_view(db, inc, with_route_for=department if with_route else None)
        return routing_policy.filter_for_department(full, department)

    @classmethod
    def citizen_view(cls, db: Session, report: EmergencyReport) -> Dict[str, Any]:
        canonical = db.get(EmergencyReport, report.merged_into_id) if report.merged_into_id else report
        ass = canonical.severity_assessments[0] if canonical.severity_assessments else None
        rec = next((r for r in canonical.recommendations if r.role == "USER"), None)
        lang = report.preferred_language or report.detected_language or "en"
        g = guidance_for(canonical.category, lang)  # guidance in THIS citizen's language
        f = cls.combined_facts(db, canonical)
        insufficient = bool(ass and any(e.get("code") == "category:other" for e in ass.evidence or [])
                            and len(ass.evidence or []) == 1)
        return {
            "incident_id": report.id,
            "canonical_incident_id": canonical.id,
            "merged": canonical.id != report.id,
            "status": canonical.status,
            "category": canonical.category,
            "created_at": report.created_at,
            "assessment": {
                "status": "complete" if report.ai_status in ("COMPLETED", "RULE_BASED", "UNAVAILABLE") else "pending",
                "method": (report.ai_extractions[0].method if report.ai_extractions else None),
                "priority_score": int(ass.priority_score) if ass else None,
                "severity": ass.severity if ass else None,
                "evidence_codes": [e.get("code") for e in (ass.evidence if ass else []) if e.get("code")],
                "insufficient_evidence": insufficient,
                "version": ass.assessment_version if ass else None,
            },
            "location": {"label": report.location, "latitude": report.latitude, "longitude": report.longitude,
                         "source": report.location_source, "verified": bool(report.coordinates_verified)},
            "language": {"detected": report.detected_language, "confidence": report.language_confidence,
                         "response_language": g["language"], "fallback": g["language_fallback"]},
            "guidance": g,
            "departments": [{"department": n.department, "status": n.status} for n in canonical.notifications
                            if n.status != "CANCELLED"],
            "updates": [cls._citizen_update(u, g["language"]) for u in canonical.updates if u.public],
            "dispatches": [DispatchService.citizen_dict(d) for d in DispatchService.active_and_recent(db, canonical)],
            "media": [{"id": m.id, "status": m.status} for m in report.media],
            "uncertainties": (ass.uncertainties if ass else [])[:4],
            "injury_certainty": f["injury_certainty"],
        }

    @staticmethod
    def _citizen_update(u, lang: str) -> Dict[str, Any]:
        import json as _json
        local = None
        if u.note and u.note_translated and lang and lang != "en":
            try:
                local = _json.loads(u.note_translated).get(lang)
            except Exception:
                local = None
        return {"at": u.created_at, "status": u.status, "department": u.department,
                "note": local or u.note, "note_original": u.note if local else None, "note_translated": bool(local)}

    @classmethod
    def translate_public_note(cls, update_id: str) -> None:
        """Background task: translate a responder's public English note into each reporter's language."""
        import json as _json
        from app.db.session import SessionLocal
        from app.services.translation_service import translate
        db = SessionLocal()
        try:
            u = db.get(IncidentUpdate, update_id)
            if not u or not u.note or not u.public:
                return
            inc = db.get(EmergencyReport, u.incident_id)
            langs = {(r.preferred_language or r.detected_language or "en") for r in cls._linked_reports(db, inc)} - {"en"}
            out = {}
            for lang in langs:
                t, _ = translate(u.note, "en", lang)
                if t:
                    out[lang] = t
            if out:
                u.note_translated, u.note_language = _json.dumps(out, ensure_ascii=False), ",".join(sorted(out))
                db.commit()
        except Exception as e:
            logger.warning(f"note translation failed for {update_id}: {e}")
            db.rollback()
        finally:
            db.close()

    # ============================================================ operations
    @classmethod
    def list_for_department(cls, db: Session, department: str, status: Optional[str], limit: int, offset: int):
        q = db.query(EmergencyReport).filter(EmergencyReport.merged_into_id.is_(None))
        if department != "ADMIN":
            q = q.join(RoutingDecision, RoutingDecision.incident_id == EmergencyReport.id).filter(
                RoutingDecision.department == department, RoutingDecision.included.is_(True),
                RoutingDecision.superseded.is_(False))
        if status == "open":
            q = q.filter(EmergencyReport.status.in_(OPEN_STATUSES))
        elif status:
            q = q.filter(EmergencyReport.status == status.upper())
        total = q.count()
        rows = q.order_by(EmergencyReport.created_at.desc()).offset(offset).limit(limit).all()
        return total, rows

    @classmethod
    def is_routed_to(cls, inc: EmergencyReport, department: str) -> bool:
        if department == "ADMIN":
            return True
        return any(d.department == department and d.included and not d.superseded for d in inc.routing_decisions)

    @classmethod
    def push_updates(cls, db: Session, canonical: EmergencyReport) -> None:
        try:
            NotificationService.dispatch_pending(db, canonical.id, lambda dep: {"incident_id": canonical.id})
            for d in canonical.routing_decisions:
                if d.included and not d.superseded:
                    manager.publish(d.department, {"type": "incident.updated", "incident_id": canonical.id})
            db.commit()
        except Exception as e:
            logger.warning(f"push_updates failed: {e}")
            db.rollback()
