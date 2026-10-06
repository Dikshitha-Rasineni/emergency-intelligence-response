"""
Immediate Reporter Guidance Engine

Provides actionable guidance to the person who reported an emergency
while waiting for emergency responders.
"""

GUIDANCE_RULES = {
    "accident": [
        "Stay in a safe location away from moving traffic and damaged vehicles.",
        "If you can do so safely, provide responders with the exact incident location.",
        "Keep the emergency access route clear for the approaching emergency team.",
        "Do not attempt risky rescue actions or move seriously injured people unless there is immediate danger.",
        "Stay available to provide additional information to emergency responders.",
    ],

    "fire": [
        "Move to a safe location away from the fire and smoke.",
        "If it is safe to do so, provide responders with the exact location and relevant information about the fire.",
        "Keep access routes clear for approaching fire and rescue vehicles.",
        "Warn nearby people about the danger only when doing so does not put you at risk.",
        "Stay at a safe location and remain available to provide information to responders.",
    ],

    "flood": [
        "Move to higher or safer ground away from rising or moving water.",
        "Provide responders with the exact location and information about people who may be affected.",
        "Keep access routes clear for approaching emergency teams.",
        "Follow instructions from emergency services and local authorities.",
        "Remain in a safe location and provide additional information if responders request it.",
    ],

    "other": [
        "Move to a safe location away from the emergency.",
        "Provide responders with the exact incident location and relevant information.",
        "Keep the emergency access route clear for responders.",
        "Avoid taking unnecessary risks while attempting to help others.",
        "Stay available to provide additional information to emergency responders.",
    ],
}


def generate_reporter_guidance(
    emergency_type: str,
    critical_indicators: list[str] | None = None,
) -> dict:
    """
    Generate immediate guidance for the person who reported an emergency.

    This component provides predefined safety-oriented guidance rather
    than allowing the language model to freely invent emergency actions.
    """

    emergency_type = (emergency_type or "other").lower().strip()

    guidance = GUIDANCE_RULES.get(
        emergency_type,
        GUIDANCE_RULES["other"],
    ).copy()

    critical_indicators = critical_indicators or []

    # Add additional guidance for specific critical situations.
    if "trapped_person" in critical_indicators:
        guidance.append(
            "Inform responders about the exact location of any trapped person "
            "and do not attempt a dangerous rescue yourself."
        )

    if "severe_bleeding" in critical_indicators:
        guidance.append(
            "Inform responders immediately if anyone has severe bleeding."
        )

    if "unconscious_person" in critical_indicators:
        guidance.append(
            "Inform responders immediately if anyone is unconscious or unresponsive."
        )

    if "building_collapse" in critical_indicators:
        guidance.append(
            "Stay away from unstable structures and inform responders about "
            "anyone who may be trapped inside."
        )

    if "rising_water" in critical_indicators:
        guidance.append(
            "Inform responders if the water level is continuing to rise or "
            "people are becoming isolated."
        )

    # Remove duplicates while preserving order.
    unique_guidance = []

    for item in guidance:
        if item not in unique_guidance:
            unique_guidance.append(item)

    return {
        "emergency_type": emergency_type,
        "guidance": unique_guidance,
        "emergency_contact": (
            "Contact local emergency services if they have not already "
            "been notified."
        ),
    }