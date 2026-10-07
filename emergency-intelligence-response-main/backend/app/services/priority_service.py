from typing import List, Dict, Any, Tuple
from app.core.config import settings


class PriorityService:
    @staticmethod
    def calculate_priority(
        description: str,
        injuries: int = 0,
        affected_people: int = 0,
        critical_indicators: List[str] = None,
        emergency_type: str = None
    ) -> Tuple[int, str, List[str]]:
        """
        Deterministic, explainable priority & severity scoring engine.
        Returns: (priority_score, severity, factors_list)
        """
        score = 25  # standard baseline for any emergency signal
        factors = ["Baseline emergency triage triage anchor (+25)"]
        lower = description.lower()
        type_lower = (emergency_type or "").lower()

        # 1. High-Acuity Medical & Life-Threat Triggers
        medical_keywords = ["unconscious", "cardiac", "heart attack", "collapsed", "not breathing", "unresponsive", "bleeding profusely", "amputation"]
        if any(kw in lower for kw in medical_keywords) or "unresponsive casualty" in (str(critical_indicators).lower()):
            score += 35
            factors.append("Critical life-threat / unconscious or unresponsive casualty detected (+35)")

        # 2. Fire, Explosion & Structural Trapped Triggers
        fire_keywords = ["fire", "smoke", "trapped", "explosion", "blaze", "burning", "gas leak"]
        if any(kw in lower for kw in fire_keywords) or "fire" in type_lower:
            score += 30
            factors.append("Active fire / smoke inhalation / trapped personnel hazard (+30)")

        # 3. High-Speed Collision & Roadway Corridors
        accident_keywords = ["accident", "crash", "collision", "overturned", "pileup", "highway"]
        if any(kw in lower for kw in accident_keywords) or "accident" in type_lower:
            score += 20
            factors.append("Corridor collision / multi-vehicle impact (+20)")

        # 4. Flood / Water hazard
        water_keywords = ["flood", "submerged", "drowning", "rising water", "waterlogging"]
        if any(kw in lower for kw in water_keywords) or "flood" in type_lower:
            score += 20
            factors.append("Water rescue / structural submersion hazard (+20)")

        # 5. Injury Multipliers
        if injuries > 0:
            inj_contrib = min(injuries * 10, 30)
            score += inj_contrib
            factors.append(f"{injuries} reported physical casualties / injuries (+{inj_contrib})")

        # 6. Affected People Scaling
        if affected_people > 0:
            aff_contrib = min(affected_people * 5, 15)
            score += aff_contrib
            factors.append(f"{affected_people} affected people on scene (+{aff_contrib})")

        # 7. Critical Indicators Matching
        if critical_indicators:
            for ind in critical_indicators:
                ind_lower = ind.lower()
                if "cylinder" in ind_lower or "chemical" in ind_lower or "hazardous" in ind_lower:
                    score += 10
                    factors.append(f"Hazard escalation indicator: {ind} (+10)")
                    break

        # Bounds: 10 to 100
        score = max(10, min(100, score))

        # Severity determination based on configurable thresholds
        if score >= settings.PRIORITY_CRITICAL_THRESHOLD:
            severity = "CRITICAL"
        elif score >= settings.PRIORITY_HIGH_THRESHOLD:
            severity = "HIGH"
        elif score >= settings.PRIORITY_MODERATE_THRESHOLD:
            severity = "MODERATE"
        else:
            severity = "LOW"

        return score, severity, factors
