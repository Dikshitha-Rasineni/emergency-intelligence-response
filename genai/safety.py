"""
Grounded emergency safety precaution engine.

This module provides controlled, emergency-type-specific safety
precautions. It does not generate new safety rules with an LLM.
"""

from typing import Any


SAFETY_RULES = {
    "accident": {
        "precautions": [
            "Move yourself to a safe location away from moving traffic and damaged vehicles.",
            "Keep a safe distance from leaking fuel, smoke, fire, or other visible hazards.",
            "Do not enter a dangerous area or approach a severely damaged vehicle unnecessarily.",
            "If it is safe to do so, keep the emergency access route clear for responders.",
            "Follow instructions from emergency services or trained responders when they arrive.",
        ],
        "avoid_actions": [
            "Do not put yourself in danger while trying to help another person.",
            "Do not move a seriously injured person unless there is an immediate danger requiring evacuation.",
            "Do not approach a vehicle if there is a suspected fuel leak, fire, or other hazardous condition.",
        ],
    },
    "fire": {
        "precautions": [
            "Move away from the fire and smoke and go toward a safe area.",
            "Warn nearby people to move away from the affected area if doing so is safe.",
            "Keep away from smoke and avoid entering the affected building or area.",
            "Use a safe evacuation route and follow instructions from emergency responders.",
            "Keep access routes clear for fire and rescue teams.",
        ],
        "avoid_actions": [
            "Do not re-enter a burning or smoke-filled building.",
            "Do not use an elevator during a building fire unless emergency responders specifically instruct you to do so.",
            "Do not attempt to fight a fire if doing so would expose you to danger.",
        ],
    },
    "flood": {
        "precautions": [
            "Move to a safe location away from rapidly moving or rising water.",
            "Follow official evacuation instructions and move toward a designated safe area when instructed.",
            "Keep away from electrical equipment, exposed wiring, and areas where electricity may be present.",
            "Keep emergency access routes clear for rescue teams.",
            "Stay informed through official emergency instructions while waiting for assistance.",
        ],
        "avoid_actions": [
            "Do not walk or drive through moving floodwater.",
            "Do not enter flooded areas where the depth or current is unknown.",
            "Do not touch electrical equipment or exposed wiring in or near floodwater.",
        ],
    },
    "other": {
        "precautions": [
            "Move to a safe location away from any immediate hazard.",
            "Keep a safe distance from the affected area.",
            "Follow instructions from emergency services or trained responders.",
            "Keep access routes clear for emergency responders.",
        ],
        "avoid_actions": [
            "Do not put yourself in danger while attempting to help.",
            "Do not enter an unsafe or restricted area.",
        ],
    },
}


CRITICAL_RULES = {
    "unconscious_person": [
        "Do not move the person unnecessarily unless there is an immediate danger.",
        "Tell emergency responders that an unconscious person is present.",
    ],
    "severe_bleeding": [
        "Tell emergency responders that severe bleeding is present.",
        "If you are trained and it is safe to do so, follow appropriate first-aid guidance while waiting for professional help.",
    ],
    "trapped_person": [
        "Do not enter an unstable or dangerous area to attempt a rescue.",
        "Tell emergency responders exactly where the trapped person is located if known.",
    ],
    "building_collapse": [
        "Stay away from unstable structures and collapsed areas.",
        "Do not enter the collapsed structure unless directed by trained rescue personnel.",
    ],
    "severe_fire": [
        "Move away from the fire and smoke.",
        "Do not enter the affected building or area.",
    ],
    "rising_water": [
        "Move away from rising or moving water toward a safe location.",
        "Do not enter moving floodwater.",
    ],
    "missing_person": [
        "Provide emergency responders with the person's last known location and relevant identifying information if known.",
        "Do not enter dangerous areas to search without appropriate training and support.",
    ],
}


def _deduplicate(items: list[str]) -> list[str]:
    seen = set()
    result = []

    for item in items:
        normalized = item.strip()

        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)

    return result


def generate_safety_precautions(
    emergency_type: str,
    critical_indicators: list[str] | None = None,
) -> dict[str, Any]:
    """
    Return grounded safety precautions for an emergency.

    The returned guidance is selected from predefined safety rules.
    No new safety instructions are generated by the LLM.
    """

    emergency_type = (emergency_type or "other").lower().strip()

    if emergency_type not in SAFETY_RULES:
        emergency_type = "other"

    critical_indicators = critical_indicators or []

    base_rules = SAFETY_RULES[emergency_type]

    precautions = list(base_rules["precautions"])
    avoid_actions = list(base_rules["avoid_actions"])
    additional_precautions = []

    normalized_indicators = {
        str(item).lower().strip()
        for item in critical_indicators
    }

    for indicator in normalized_indicators:
        rules = CRITICAL_RULES.get(indicator)

        if not rules:
            continue

        for rule in rules:
            additional_precautions.append(rule)

    precautions = _deduplicate(
        precautions + additional_precautions
    )

    avoid_actions = _deduplicate(avoid_actions)

    return {
        "emergency_type": emergency_type,
        "precautions": precautions,
        "avoid_actions": avoid_actions,
    }
