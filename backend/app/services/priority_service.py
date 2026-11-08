"""
Transparent, versioned priority engine (rules-v2).

This is an operational *priority* score for queue ordering, not a medical triage
score. Every point added is recorded as evidence with its source. Corroborating
evidence from images or sensors adds a small, capped amount because it is
correlated with the citizen report, not independent confirmation.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from app.core.config import settings

VERSION = "rules-v2"

CATEGORY_BASE = {
    "medical": 35, "fire": 40, "gas_leak": 35, "road_accident": 30, "flood": 30,
    "structural_collapse": 40, "rescue": 35, "security": 30, "sos": 30, "other": 15,
}
HAZARD_POINTS = {"fire": 10, "gas": 10, "fuel_leak": 10, "chemical": 10, "structural": 10,
                 "weapon": 15, "electrical": 5, "smoke": 5, "flood_water": 5}


def severity_for(score: int) -> str:
    if score >= settings.PRIORITY_CRITICAL_THRESHOLD:
        return "CRITICAL"
    if score >= settings.PRIORITY_HIGH_THRESHOLD:
        return "HIGH"
    if score >= settings.PRIORITY_MODERATE_THRESHOLD:
        return "MODERATE"
    return "LOW"


class PriorityService:
    @staticmethod
    def assess(
        category: str,
        injuries: int,
        injury_certainty: str,
        affected_people: int,
        hazards: List[str],
        trapped: bool,
        unconscious: bool,
        image_findings: Optional[List[Dict[str, Any]]] = None,
        sensor_events: Optional[List[Dict[str, Any]]] = None,
        location_verified: bool = True,
        extra_uncertainties: Optional[List[str]] = None,
        report_source: str = "user_report",
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        evidence: List[Dict[str, Any]] = []

        def add(factor: str, points: int, source: str = report_source, code: str = ""):
            evidence.append({"factor": factor, "points": points, "source": source, "observed_at": now, "code": code})

        base = CATEGORY_BASE.get(category, CATEGORY_BASE["other"])
        add(f"Category baseline: {category}", base, code=f"category:{category}")
        if unconscious:
            add("Person reported unconscious or not breathing", 30, code="unconscious")
        if trapped:
            add("People reported trapped", 20, code="trapped")
        if injuries > 0 and injury_certainty == "confirmed":
            add(f"{injuries} injured reported", min(5 * injuries, 20), code=f"injuries:{injuries}")
        elif injuries > 0 and injury_certainty == "possible":
            add("Possible injuries reported (unconfirmed)", 5, code="injuries_possible")
        if affected_people >= 20:
            add(f"{affected_people} people affected", 15, code=f"affected:{affected_people}")
        elif affected_people >= 5:
            add(f"{affected_people} people affected", 10, code=f"affected:{affected_people}")
        for h in sorted(set(hazards or [])):
            if h in HAZARD_POINTS and not (h == "fire" and category == "fire"):
                add(f"Hazard reported: {h}", HAZARD_POINTS[h], code=f"hazard:{h}")

        # Corroboration (capped; correlated evidence is not independent confirmation)
        img_pts = 0
        for f in image_findings or []:
            if img_pts >= 10:
                break
            if f.get("supports_category") and f.get("confidence_level") in ("high", "medium"):
                add(f"Image shows: {f.get('finding')}", 5, source=f"image:{f.get('media_id', '')[:8]}", code="image_corroboration")
                img_pts += 5
        sens_pts = 0
        for s in sensor_events or []:
            if sens_pts >= 10:
                break
            add(f"Qualified sensor alert: {s.get('reason') or s.get('event_type')}", 5,
                source=f"iot:{s.get('device_id')}", code="sensor_corroboration")
            sens_pts += 5
        if any(s.get("severe") for s in sensor_events or []):
            add("Sensor graded the reading severe (high impact / high heat or smoke)", 15,
                source="iot", code="sensor_severe")

        score = max(0, min(100, sum(e["points"] for e in evidence)))
        uncertainties = list(dict.fromkeys(extra_uncertainties or []))
        if not location_verified:
            uncertainties.append("Location not verified")
        if injury_certainty == "unknown" or (injuries == 0 and injury_certainty == "none_reported"):
            uncertainties.append("Injury status not reported")
        insufficient = category == "other" and not hazards and not trapped and not unconscious and injuries == 0
        return {
            "score": score,
            "severity": severity_for(score),
            "evidence": evidence,
            "factors": [f"{e['factor']} (+{e['points']}, {e['source']})" for e in evidence],
            "uncertainties": uncertainties,
            "insufficient_evidence": insufficient,
            "version": VERSION,
            "assessed_at": now,
        }

    # Backwards-compatible signature used by older callers/tests
    @staticmethod
    def calculate_priority(description: str, injuries: int = 0, affected_people: int = 0,
                           critical_indicators: List[str] = None, emergency_type: str = None) -> Tuple[int, str, List[str]]:
        from app.services.ai_service import AIService
        from app.services.taxonomy import normalize_category
        ex = AIService.extract(description, "en", use_llm=False)
        cat = normalize_category(emergency_type) if emergency_type else ex.category
        ind = " ".join(critical_indicators or []).lower()
        r = PriorityService.assess(
            category=cat, injuries=max(injuries, ex.injuries),
            injury_certainty="confirmed" if injuries else ex.injury_certainty,
            affected_people=max(affected_people, ex.affected_people), hazards=ex.hazards,
            trapped=ex.trapped or "trapped" in ind, unconscious=ex.unconscious_or_not_breathing or "unconscious" in ind,
        )
        return r["score"], r["severity"], r["factors"]
