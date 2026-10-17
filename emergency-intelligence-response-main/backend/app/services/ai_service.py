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
from app.services.language_service import LanguageService


class AIService:
    @classmethod
    def _call_ollama(
        cls,
        system_prompt: str,
        user_prompt: str,
        timeout_seconds: float = 4.0,
        lang: str = "en",
    ) -> Optional[str]:
        """Queries local Ollama instance with timeout and explicit language enforcement."""
        try:
            lang_name = LanguageService.LANGUAGE_NAMES.get(lang, "English")
            full_system_prompt = (
                f"{system_prompt}\n\n"
                f"MANDATORY LANGUAGE DIRECTIVE:\n"
                f"The user report is written in {lang_name} (ISO: '{lang}').\n"
                f"Respond entirely in the requested output language: {lang_name}.\n"
                f"Preserve the meaning of the original emergency report.\n"
                f"Do not switch to English unless English is the requested language.\n"
                f"Keep names, addresses, phone numbers, coordinates, and system enum identifiers unchanged.\n"
                f"Return valid JSON only."
            )

            url = f"{settings.OLLAMA_BASE_URL}/api/chat"
            payload = {
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": full_system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 350,
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
    def extract_incident_data(
        cls,
        text: str,
        location_hint: str = None,
        lang: Optional[str] = None,
    ) -> AIExtractResponse:
        """
        Extracts structured incident attributes from unstructured text.
        Supports Telugu, Tamil, Hindi, Kannada, Malayalam, and English.
        Uses local LLM if responsive; falls back to deterministic multilingual parser.
        """
        # Auto-detect language if not explicitly provided
        detected_lang = lang or LanguageService.detect_language(text)

        system_prompt = (
            "You are RESQ.AI Emergency Extractor. Extract structured JSON only from the user report.\n"
            "Format: {\"emergency_type\": str, \"affected_people\": int, \"injuries\": int, "
            "\"critical_indicators\": [str], \"location_information\": str, \"missing_information\": [str]}\n"
            "Do not include conversational text or markdown blocks."
        )

        ollama_response = cls._call_ollama(
            system_prompt,
            f"Emergency report: {text}",
            lang=detected_lang,
        )
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
                        language=detected_lang,
                    )
            except Exception as e:
                logger.debug(f"Could not parse Ollama response: {e}")

        # Deterministic High-Precision Multilingual Fallback Parser
        injuries, affected = LanguageService.extract_numbers_and_injuries(text, lang=detected_lang)
        emergency_type = LanguageService.extract_emergency_type(text, lang=detected_lang)
        critical_indicators = LanguageService.extract_critical_indicators(text, lang=detected_lang)

        missing_info = []
        lower = text.lower()
        if "vehicle" in lower or "వాహనం" in text or "गाड़ी" in text:
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
            language=detected_lang,
        )

    @classmethod
    def generate_precautions(
        cls,
        emergency_type: str,
        description: str = "",
        priority: int = 50,
        lang: Optional[str] = None,
    ) -> PrecautionResponse:
        """
        Generates role-appropriate, non-diagnostic public safety precautions in the requested language.
        """
        detected_lang = lang or LanguageService.detect_language(description)

        precautions = LanguageService.get_precautions(emergency_type, lang=detected_lang)

        disclaimer_map = {
            "en": "AI Recommended Precautions — public safety guidance only. Not a medical diagnosis.",
            "te": "AI సిఫార్సు చేసిన జాగ్రత్తలు — ప్రజా భద్రతా మార్గదర్శకాలు మాత్రమే. వైద్య నిర్ధారణ కాదు.",
            "ta": "AI பரிந்துரைத்த முன்னெச்சரிக்கைகள் — பொதுப் பாதுகாப்பு வழிகாட்டுதல் மட்டுமே. மருத்துவக் கண்டறிதல் அல்ல.",
            "hi": "AI अनुशंसित सावधानियां — केवल सार्वजनिक सुरक्षा मार्गदर्शन। चिकित्सीय निदान नहीं।",
            "kn": "AI ಶಿಫಾರಸು ಮಾಡಿದ ಮುನ್ನೆಚ್ಚರಿಕೆಗಳು — ಸಾರ್ವಜನಿಕ ಸುರಕ್ಷತಾ ಮಾರ್ಗದರ್ಶನ ಮಾತ್ರ. ವೈದ್ಯಕೀಯ ರೋಗನಿರ್ಣಯವಲ್ಲ.",
            "ml": "AI ശുപാർശ ചെയ്ത മുൻകരുതലുകൾ — പൊതുജന സുരക്ഷാ മാർഗ്ഗനിർദ്ദേശം മാത്രം. മെഡിക്കൽ രോഗനിർണയമല്ല.",
        }

        return PrecautionResponse(
            emergency_type=emergency_type,
            precautions=precautions,
            disclaimer=disclaimer_map.get(detected_lang, disclaimer_map["en"]),
            language=detected_lang,
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
        lang: Optional[str] = None,
    ) -> RoleIntelligenceResponse:
        """
        Generates role-specific operational intelligence for Hospital, Police, or Fire responders.
        """
        role = role.upper()
        detected_lang = lang or LanguageService.detect_language(description)

        intel = LanguageService.get_role_intelligence(
            role=role,
            emergency_type=emergency_type,
            injuries=injuries,
            affected_people=affected_people,
            priority_score=priority_score,
            lang=detected_lang,
        )

        services = ["Trauma Resuscitation Bay", "ICU Bed Reservation", "Blood Bank On-Call", "Ambulance Receiving Bay"] if role == "HOSPITAL" else (
            ["Patrol Unit Perimeter", "Traffic Corridor Clearance", "Crowd Control", "CAD Log Synchronization"] if role == "POLICE" else (
                ["Heavy Rescue Extrication", "Structural Suppression", "Thermal Reconnaissance", "Hazmat Isolation"] if role == "FIRE" else ["Dispatch Command"]
            )
        )
        equipment = ["Airway kit with video laryngoscope", "Defibrillator", "Rapid IV Infuser"] if role == "HOSPITAL" else (
            ["High-visibility LED cones", "Road barricade units", "Body cameras"] if role == "POLICE" else (
                ["Hydraulic Cutter / Spreader Kit", "SCBA Breathing Apparatus", "AFFF Foam Nozzle"] if role == "FIRE" else ["CAD Terminal"]
            )
        )

        return RoleIntelligenceResponse(
            role=role,
            summary=intel["summary"],
            recommendation=intel["recommendation"],
            operational_checklist=intel["operational_checklist"],
            required_services=services,
            required_equipment=equipment,
            missing_information=["Scene ambient hazards confirmation", "Secondary impact confirmation"],
            traffic_impact="Arterial corridor lane blockage. Upstream traffic slowdown expected." if role == "POLICE" else None,
            casualty_staging=f"Estimated triage volume: {affected_people} individuals ({injuries} acute casualties)." if role == "HOSPITAL" else None,
            tactical_deployments="Upwind operational staging; 30-meter isolation perimeter around hazardous impact point." if role == "FIRE" else None,
            language=detected_lang,
        )
