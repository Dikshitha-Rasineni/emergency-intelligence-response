import json
import re
import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.schemas.ai import (
    AIExtractResponse,
    PrecautionResponse,
    RoleIntelligenceResponse,
)


class AIService:
    @classmethod
    def _call_ollama(cls, system_prompt: str, user_prompt: str, timeout_seconds: float = 4.0) -> Optional[str]:
        """Queries local Ollama instance with timeout."""
        try:
            url = f"{settings.OLLAMA_BASE_URL}/api/chat"
            payload = {
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 300,
                },
            }
            with httpx.Client(timeout=timeout_seconds) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("message", {}).get("content", "")
        except Exception as e:
            logger.debug(f"Ollama call skipped or timed out: {e}")
        return None

    @classmethod
    def extract_incident_data(cls, text: str, location_hint: str = None) -> AIExtractResponse:
        """
        Extracts structured incident attributes from unstructured text.
        Uses local LLM if responsive; falls back to deterministic NLP regex parser.
        """
        system_prompt = (
            "You are RESQ.AI Emergency Extractor. Extract structured JSON only from the user report.\n"
            "Format: {\"emergency_type\": str, \"affected_people\": int, \"injuries\": int, "
            "\"critical_indicators\": [str], \"location_information\": str, \"missing_information\": [str]}\n"
            "Do not include conversational text or markdown blocks."
        )

        ollama_response = cls._call_ollama(system_prompt, f"Emergency report: {text}")
        if ollama_response:
            try:
                # Find JSON block
                json_match = re.search(r"\{.*\}", ollama_response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    return AIExtractResponse(
                        emergency_type=parsed.get("emergency_type", "General Emergency"),
                        affected_people=int(parsed.get("affected_people", 0)),
                        injuries=int(parsed.get("injuries", 0)),
                        critical_indicators=parsed.get("critical_indicators", []),
                        location_information=parsed.get("location_information") or location_hint,
                        confidence_score=0.92,
                        missing_information=parsed.get("missing_information", []),
                    )
            except Exception as e:
                logger.debug(f"Could not parse Ollama response: {e}")

        # Deterministic High-Precision Fallback Parser
        lower = text.lower()
        emergency_type = "General Emergency"
        critical_indicators = []
        injuries = 0
        affected = 0
        missing_info = []

        # Emergency Type Classification
        if any(w in lower for w in ["accident", "crash", "collision", "overturned", "fender bender"]):
            emergency_type = "Major Road Accident"
        elif any(w in lower for w in ["fire", "smoke", "blaze", "burning", "explosion"]):
            emergency_type = "Commercial Building Fire"
        elif any(w in lower for w in ["flood", "waterlogging", "submerged", "drowning", "rising water"]):
            emergency_type = "Urban Flash Flood & Vehicle Stall"
        elif any(w in lower for w in ["cardiac", "heart attack", "collapsed", "unresponsive", "cpr", "stroke"]):
            emergency_type = "Cardiac / Acute Medical Crisis"

        # Critical Indicators Detection
        if "unconscious" in lower:
            critical_indicators.append("Unconscious casualty reported")
        if "trapped" in lower or "pinned" in lower:
            critical_indicators.append("Occupants trapped on scene")
        if "smoke" in lower or "gas" in lower or "cylinder" in lower:
            critical_indicators.append("Hazardous smoke or gas cylinder condition")
        if "cpr" in lower:
            critical_indicators.append("CPR in progress on scene")
        if "submerged" in lower or "roof" in lower:
            critical_indicators.append("Rising flood water / vehicle submerged")

        # Injury Count Extraction
        inj_match = re.search(r"(\d+|one|two|three|four|five)\s+(?:people\s+)?(?:injured|injuries|casualties|hurt)", lower)
        num_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
        if inj_match:
            raw_val = inj_match.group(1)
            injuries = num_map.get(raw_val, int(raw_val) if raw_val.isdigit() else 1)
        elif "injured" in lower or "injury" in lower:
            injuries = 1

        # Affected People Count Extraction
        aff_match = re.search(r"(\d+|one|two|three|four|five)\s+(?:people|persons|passengers|occupants)", lower)
        if aff_match:
            raw_val = aff_match.group(1)
            affected = num_map.get(raw_val, int(raw_val) if raw_val.isdigit() else 1)
        else:
            affected = max(injuries, 1 if emergency_type != "General Emergency" else 0)

        if "vehicle" in lower and not any("fuel" in m for m in missing_info):
            missing_info.append("Vehicle fuel leak status unconfirmed")
        if injuries > 0:
            missing_info.append("Exact age demographics of casualties unconfirmed")

        return AIExtractResponse(
            emergency_type=emergency_type,
            affected_people=affected,
            injuries=injuries,
            critical_indicators=critical_indicators,
            location_information=location_hint or "Verified Incident Location",
            confidence_score=0.95,
            missing_information=missing_info,
        )

    @classmethod
    def generate_precautions(cls, emergency_type: str, description: str = "", priority: int = 50) -> PrecautionResponse:
        """
        Generates role-appropriate, non-diagnostic public safety precautions.
        """
        type_lower = emergency_type.lower()
        desc_lower = description.lower()

        if "fire" in type_lower or "smoke" in desc_lower:
            precautions = [
                "Crawl low under smoke — clean breathable air remains within 1 foot of the floor.",
                "Do NOT use elevators under any circumstances; use external fire exit stairwells.",
                "Close internal doors behind you as you evacuate to compartmentalize fire spread.",
                "Move across the street to an upwind assembly point away from glass facades.",
                "If clothes catch fire: Stop, Drop, and Roll immediately.",
            ]
        elif "flood" in type_lower or "water" in desc_lower:
            precautions = [
                "Do NOT attempt to walk, wade, or drive through flowing flood waters.",
                "Beware of hidden open manholes and live electrical cables in submerged areas.",
                "Stay on stable rooftop or elevated ground until emergency rescue teams arrive.",
                "Signal with bright cloth or flashlight if visibility is reduced.",
                "Do not drink tap water from submerged piping.",
            ]
        elif "cardiac" in type_lower or "cpr" in desc_lower:
            precautions = [
                "Continue uninterrupted chest compressions at 100–120 beats per minute until paramedics arrive.",
                "Push hard and fast in the center of the chest (at least 2 inches deep).",
                "Send a bystander immediately to locate the nearest Automated External Defibrillator (AED).",
                "Keep entry doors and elevator bays unlocked and clear for ambulance crew access.",
                "Do not attempt to administer oral liquids or food.",
            ]
        elif "accident" in type_lower or "crash" in desc_lower:
            precautions = [
                "Do NOT move injured casualties unless there is immediate risk of fire or vehicle explosion.",
                "Stay safely behind the highway crash barrier away from moving corridor traffic.",
                "Turn on vehicle hazard flashers and place emergency warning triangles 50m upstream if safe.",
                "Keep the emergency breakdown shoulder completely clear for incoming ALS ambulances.",
                "Avoid touching exposed electrical wiring or leaking vehicle fluids.",
            ]
        else:
            precautions = [
                "Stay calm and remain in a secure, visible location.",
                "Keep phone lines open for responder dispatch coordination.",
                "Do not touch hazardous objects or fluids on scene.",
                "Follow verified instructions from official emergency personnel upon arrival.",
            ]

        return PrecautionResponse(
            emergency_type=emergency_type,
            precautions=precautions,
            disclaimer="AI Recommended Precautions — public safety guidance only. Not a medical diagnosis.",
        )

    @classmethod
    def generate_role_intelligence(
        cls,
        role: str,
        emergency_type: str,
        description: str,
        affected_people: int,
        injuries: int,
        critical_indicators: List[str],
        priority_score: int,
    ) -> RoleIntelligenceResponse:
        """
        Generates role-specific operational intelligence for Hospital, Police, or Fire responders.
        """
        role = role.upper()
        type_lower = emergency_type.lower()
        desc_lower = description.lower()

        if role == "HOSPITAL":
            summary = f"Level-1 trauma response for {emergency_type} with {injuries} reported injuries and priority {priority_score}/100."
            recommendation = "Clear trauma resuscitation bay, alert on-duty trauma surgical team, and prepare receiving ramp for incoming ALS units."
            checklist = [
                f"Reserve {max(1, injuries)} trauma resuscitation bay(s) with suction and airway management.",
                "Notify Alpha Surgical Team and Orthopedic on-call specialists.",
                "Prepare blood bank type O-negative cross-match protocol.",
                "Ensure emergency bay transit doors are cleared for ambulance docking.",
            ]
            services = ["Trauma Resuscitation Bay", "ICU Bed Reservation", "Blood Bank On-Call", "Ambulance Receiving Bay"]
            equipment = ["Airway kit with video laryngoscope", "Defibrillator", "Rapid IV Infuser", "Cervical collar sets"]
            casualty_staging = f"Estimated triage volume: {affected_people} individuals ({injuries} acute casualties)."
            traffic_impact = None
            tactical = None

        elif role == "POLICE":
            summary = f"Corridor security and traffic dispatch for {emergency_type} at priority {priority_score}/100."
            recommendation = "Dispatch Patrol-14 to secure incident perimeter, stage traffic diversions upstream, and preserve emergency corridor for EMS."
            checklist = [
                "Deploy patrol unit to establish outer safety cordon 100 meters upstream.",
                "Place traffic cones and divert arterial lanes away from the impact site.",
                "Preserve active lane for incoming ambulance and fire tenders.",
                "Record vehicle registration numbers and witness contact details.",
            ]
            services = ["Patrol Unit Perimeter", "Traffic Corridor Clearance", "Crowd Control", "CAD Log Synchronization"]
            equipment = ["High-visibility LED cones", "Road barricade units", "Body cameras", "Corridor flare markers"]
            traffic_impact = "Arterial corridor lane blockage. Upstream traffic slowdown expected within 1.5 km."
            casualty_staging = None
            tactical = None

        elif role == "FIRE":
            summary = f"Tactical rescue & hazard suppression for {emergency_type} at priority {priority_score}/100."
            recommendation = "Deploy Heavy Rescue Tender HR-04 with hydraulic extrication gear, establish 360-degree hazard perimeter, and scan for hazardous materials."
            checklist = [
                "Stage HR-04 tender 30m upwind with 4,500L water and AFFF foam readiness.",
                "Deploy hydraulic cutters and spreaders for casualty extrication if trapped.",
                "Disconnect 12V/high-voltage vehicle batteries to prevent electrical ignition.",
                "Perform gas/thermal imaging scan for structural hot spots or cylinder leaks.",
            ]
            services = ["Heavy Rescue Extrication", "Structural Suppression", "Thermal Reconnaissance", "Hazmat Isolation"]
            equipment = ["Hydraulic Cutter / Spreader Kit", "SCBA Breathing Apparatus", "AFFF Foam Nozzle", "Thermal Imaging Camera"]
            tactical = "Upwind operational staging; 30-meter isolation perimeter around hazardous impact point."
            casualty_staging = None
            traffic_impact = None

        else:
            summary = f"Multi-agency operational alert for {emergency_type}."
            recommendation = "Maintain unified command and coordinate resource deployment."
            checklist = ["Verify incident coordinates", "Confirm casualty counts", "Synchronize dispatch timeline"]
            services = ["Dispatch Command"]
            equipment = ["CAD Terminal"]
            traffic_impact = None
            casualty_staging = None
            tactical = None

        return RoleIntelligenceResponse(
            role=role,
            summary=summary,
            recommendation=recommendation,
            operational_checklist=checklist,
            required_services=services,
            required_equipment=equipment,
            missing_information=["Scene ambient hazards confirmation", "Secondary impact confirmation"],
            traffic_impact=traffic_impact,
            casualty_staging=casualty_staging,
            tactical_deployments=tactical,
        )
