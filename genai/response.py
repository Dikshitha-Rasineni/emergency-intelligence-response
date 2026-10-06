"""
GenAI Response and Incident Report Generation

Provides two related GenAI capabilities:

3.6 - Response Recommendation
3.7 - Incident Report Generation

The same verified incident context is used for both outputs.

Severity, priority, and ranked resources are optional so the
module can work now and integrate with the ML/resource modules later.

Multilingual output:
    Qwen always reasons in English. For non-English reports, the
    human-readable text fields are translated back into the
    reporter's language and returned under the additive
    "localized" key. English output is unchanged.
"""

import json

from genai.extractor import load_model, MODEL_LOCK, prepare_emergency_text
from genai.language import detect_language
from genai.translator import SUPPORTED_LANGUAGES, translate_from_english


# -------------------------------------------------------------------
# Shared helper
# -------------------------------------------------------------------


def _generate(prompt: str, max_tokens: int = 500) -> str:
    """
    Generate a response using the local Qwen model.

    llama.cpp is not safe for concurrent access to the same model
    instance, so inference is protected by the shared MODEL_LOCK.
    """

    model = load_model()

    with MODEL_LOCK:
        output = model.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an emergency intelligence assistant. "
                        "Use only the information provided in the incident "
                        "context. Do not invent facts, resources, casualties, "
                        "locations, severity, or actions. "
                        "Return concise, structured information."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_tokens=max_tokens,
            temperature=0.1,
        )

    return output["choices"][0]["message"]["content"].strip()


def _parse_json(text: str) -> dict:
    """
    Safely parse JSON returned by the model.
    """

    text = text.strip()

    # Remove markdown code fences if Qwen adds them.
    if text.startswith("```"):
        text = text.replace("```json", "", 1)
        text = text.replace("```", "", 1)
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "raw_response": text
        }


# -------------------------------------------------------------------
# Multilingual helpers (reuse existing detection / translation)
# -------------------------------------------------------------------


def _resolve_languages(
    incident_description: str,
    output_language: str | None,
) -> tuple[str, str]:
    """
    Returns (english_description, response_language).

    - English input: description is returned unchanged.
    - Non-English input: translated with the existing pipeline.
    - If the translator service is unavailable, falls back to the
      original text so the English-only behavior never breaks.
    """

    try:
        prepared = prepare_emergency_text(incident_description)
        english_description = prepared["translated_text"]
        detected = prepared["source_language"]
    except RuntimeError:
        english_description = incident_description
        detected = detect_language(incident_description)

    language = detected

    if output_language:
        for supported in SUPPORTED_LANGUAGES | {"English"}:
            if supported.lower() == output_language.strip().lower():
                language = supported
                break

    return english_description, language


def _localize_fields(fields: dict, language: str) -> dict | None:
    """
    Translate human-readable string / list-of-string fields
    from English into `language`.

    Returns None for English or unsupported languages.
    Never raises: translation failure is reported in the result
    so the English response is still delivered.
    """

    if not language or language not in SUPPORTED_LANGUAGES:
        return None

    try:
        localized = {}

        for key, value in fields.items():
            if isinstance(value, str):
                localized[key] = (
                    translate_from_english(value, language)
                    if value.strip()
                    else value
                )
            elif isinstance(value, list):
                localized[key] = [
                    translate_from_english(item, language)
                    if isinstance(item, str) and item.strip()
                    else item
                    for item in value
                ]
            else:
                localized[key] = value

        return {
            "language": language,
            "translation_status": "ok",
            "fields": localized,
        }

    except Exception as exc:
        # Includes socket timeouts / bad JSON from the translator, not just
        # RuntimeError, so the English response is always still delivered.
        return {
            "language": language,
            "translation_status": "failed",
            "error": str(exc),
            "fields": None,
        }


# -------------------------------------------------------------------
# 3.6 - GenAI Response Generation
# -------------------------------------------------------------------


def generate_response_recommendation(
    incident_description: str,
    emergency_type: str,
    affected_people: int,
    injuries: int,
    critical_indicators: list[str],
    location: str | None = None,
    severity: str | None = None,
    priority: str | None = None,
    ranked_resources: list[dict] | None = None,
    missing_information: list[str] | None = None,
    output_language: str | None = None,
) -> dict:
    """
    Generate a concise emergency response recommendation.

    Severity, priority, ranked resources, and missing information
    are optional so this function can be integrated with the ML
    and resource-ranking modules later.

    output_language: optional. If omitted, it is detected from
    incident_description. English output is unchanged.
    """

    ranked_resources = ranked_resources or []
    missing_information = missing_information or []
    critical_indicators = critical_indicators or []

    english_description, response_language = _resolve_languages(
        incident_description,
        output_language,
    )

    context = {
        "incident_description": english_description,
        "emergency_type": emergency_type,
        "affected_people": affected_people,
        "injuries": injuries,
        "critical_indicators": critical_indicators,
        "location": location,
        "severity": severity,
        "priority": priority,
        "ranked_resources": ranked_resources,
        "missing_information": missing_information,
    }

    prompt = f"""
Analyze the following verified emergency incident information.

INCIDENT CONTEXT:

{json.dumps(context, indent=2)}

Generate a concise emergency response recommendation.

Rules:

1. Use only information present in the context.
2. Do not invent resources or facts.
3. If severity or priority is not provided, state "not available".
4. If ranked resources are empty, do not invent resource names.
5. Clearly distinguish verified information from recommendations.
6. Keep the response suitable for an emergency response dashboard.
7. Return ONLY valid JSON.

Required JSON format:

{{
    "situation_summary": "Short summary of the incident",
    "recommended_response": [
        "Action or recommendation 1",
        "Action or recommendation 2"
    ],
    "resource_recommendation": [
        "Resource recommendation based only on supplied resources"
    ],
    "severity": "value or not available",
    "priority": "value or not available",
    "reasoning": "Short explanation based on available information",
    "information_gaps": [
        "Missing information that may affect response"
    ]
}}
"""

    raw_response = _generate(
        prompt,
        max_tokens=500,
    )

    result = _parse_json(raw_response)

    output = {
        "situation_summary": result.get(
            "situation_summary",
            "Emergency incident reported.",
        ),
        "recommended_response": result.get(
            "recommended_response",
            [],
        ),
        "resource_recommendation": result.get(
            "resource_recommendation",
            [],
        ),
        "severity": result.get(
            "severity",
            severity or "not available",
        ),
        "priority": result.get(
            "priority",
            priority or "not available",
        ),
        "reasoning": result.get(
            "reasoning",
            "",
        ),
        "information_gaps": result.get(
            "information_gaps",
            missing_information,
        ),
    }

    # Additive multilingual output (translation happens outside
    # MODEL_LOCK, so it never blocks other Qwen requests).
    localized = _localize_fields(
        {
            "situation_summary": output["situation_summary"],
            "recommended_response": output["recommended_response"],
            "resource_recommendation": output["resource_recommendation"],
            "reasoning": output["reasoning"],
            "information_gaps": output["information_gaps"],
        },
        response_language,
    )

    if localized is not None:
        output["response_language"] = response_language
        output["localized"] = localized

    return output


# -------------------------------------------------------------------
# 3.7 - Incident Report Generation
# -------------------------------------------------------------------


def generate_incident_report(
    incident_description: str,
    emergency_type: str,
    affected_people: int,
    injuries: int,
    critical_indicators: list[str],
    location: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    severity: str | None = None,
    priority: str | None = None,
    ranked_resources: list[dict] | None = None,
    response_recommendation: dict | None = None,
    missing_information: list[str] | None = None,
    output_language: str | None = None,
) -> dict:
    """
    Generate a structured incident report from verified incident data.

    output_language: optional. If omitted, it is detected from
    incident_description. English output is unchanged.
    """

    ranked_resources = ranked_resources or []
    missing_information = missing_information or []
    critical_indicators = critical_indicators or []
    response_recommendation = response_recommendation or {}

    english_description, response_language = _resolve_languages(
        incident_description,
        output_language,
    )

    context = {
        "incident_description": english_description,
        "emergency_type": emergency_type,
        "affected_people": affected_people,
        "injuries": injuries,
        "critical_indicators": critical_indicators,
        "location": location,
        "latitude": latitude,
        "longitude": longitude,
        "severity": severity,
        "priority": priority,
        "ranked_resources": ranked_resources,
        "response_recommendation": response_recommendation,
        "missing_information": missing_information,
    }

    prompt = f"""
Generate a structured emergency incident report using the
following verified information.

INCIDENT CONTEXT:

{json.dumps(context, indent=2)}

Rules:

1. Do not invent facts.
2. Do not change numerical values.
3. Do not invent severity, priority, resources, casualties,
   locations, or response actions.
4. Use "not available" when information was not supplied.
5. The report must be concise and suitable for an emergency
   response dashboard.
6. Return ONLY valid JSON.

Required JSON format:

{{
    "incident_summary": "Concise incident summary",
    "emergency_type": "Emergency type",
    "location": "Location or not available",
    "affected_people": 0,
    "injuries": 0,
    "critical_indicators": [],
    "severity": "Severity or not available",
    "priority": "Priority or not available",
    "resources": [],
    "response_recommendation": [],
    "information_gaps": [],
    "report_summary": "Final concise report summary"
}}
"""

    raw_response = _generate(
        prompt,
        max_tokens=600,
    )

    result = _parse_json(raw_response)

    output = {
        "incident_summary": result.get(
            "incident_summary",
            english_description,
        ),
        "emergency_type": result.get(
            "emergency_type",
            emergency_type,
        ),
        "location": result.get(
            "location",
            location or "not available",
        ),
        "affected_people": affected_people,
        "injuries": injuries,
        "critical_indicators": critical_indicators,
        "severity": result.get(
            "severity",
            severity or "not available",
        ),
        "priority": result.get(
            "priority",
            priority or "not available",
        ),
        "resources": result.get(
            "resources",
            ranked_resources,
        ),
        "response_recommendation": result.get(
            "response_recommendation",
            response_recommendation.get(
                "recommended_response",
                [],
            ),
        ),
        "information_gaps": result.get(
            "information_gaps",
            missing_information,
        ),
        "report_summary": result.get(
            "report_summary",
            english_description,
        ),
    }

    # Only free-text fields are translated. Numbers, severity,
    # priority, indicators, location and resources stay as-is.
    localized = _localize_fields(
        {
            "incident_summary": output["incident_summary"],
            "response_recommendation": output["response_recommendation"],
            "information_gaps": output["information_gaps"],
            "report_summary": output["report_summary"],
        },
        response_language,
    )

    if localized is not None:
        output["response_language"] = response_language
        output["localized"] = localized

    return output