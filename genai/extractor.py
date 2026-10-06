import json
import re

from functools import lru_cache
from threading import Lock
from pathlib import Path

from llama_cpp import Llama


from .prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    MISSING_INFORMATION_SYSTEM_PROMPT,
    MULTILINGUAL_EMERGENCY_SYSTEM_PROMPT,
)

from .language import detect_language
from .translator import translate_to_english


MODEL_PATH = (
    Path(__file__).resolve().parent
    / "models"
    / "qwen2.5-3b-instruct-q4_k_m.gguf"
)

MODEL_LOCK = Lock()

MAX_NEW_TOKENS = 200
MISSING_INFO_MAX_TOKENS = 300
MULTILINGUAL_MAX_NEW_TOKENS = 300


# ============================================================
# QWEN MODEL
# ============================================================

@lru_cache(maxsize=1)
def load_model():
    print(f"Loading local GenAI model: {MODEL_PATH}")

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}"
        )

    llm = Llama(
        model_path=str(MODEL_PATH),
        n_ctx=2048,
        n_threads=8,
        n_gpu_layers=-1,
        verbose=False,
    )

    print("GenAI model loaded successfully.")

    return llm


# ============================================================
# MULTILINGUAL PREPROCESSING
# ============================================================

def prepare_emergency_text(text: str) -> dict:
    """
    Detect the source language and translate supported
    native Indic-language text into English.

    English is passed directly to Qwen.

    Supported native languages:
        - Tamil
        - Telugu
        - Kannada
        - Malayalam
        - Hindi

    Romanized Indic languages are intentionally not handled
    here because the current transliteration pipeline was
    not reliable enough during validation.
    """

    if not text or not text.strip():
        return {
            "original_text": text,
            "translated_text": text,
            "source_language": "English",
        }

    source_language = detect_language(text)

    if source_language == "English":
        return {
            "original_text": text,
            "translated_text": text,
            "source_language": "English",
        }

    translated_text = translate_to_english(
        text,
        source_language,
    )

    return {
        "original_text": text,
        "translated_text": translated_text,
        "source_language": source_language,
    }


# ============================================================
# LLAMA RESPONSE / JSON EXTRACTION
# ============================================================

_JSON_DECODER = json.JSONDecoder()

_FENCE_OPEN = re.compile(r"^\s*```[a-zA-Z0-9_-]*\s*")
_FENCE_CLOSE = re.compile(r"\s*```\s*$")


def get_message_content(response: dict) -> str:
    """
    Safely pull the assistant text out of a llama.cpp
    create_chat_completion() response.
    """

    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(
            f"Unexpected llama.cpp response format: {response!r}"
        ) from exc

    if content is None:
        raise ValueError("GenAI response content was empty.")

    if isinstance(content, list):
        # Some builds return a list of content parts.
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )

    return str(content)


def extract_json(text: str, _depth: int = 0) -> dict:
    """
    Extract the first JSON object from the model response.

    Handles:
        - plain JSON
        - JSON surrounded by extra text
        - ```json ... ``` markdown fences
        - whitespace / newlines / escaped characters
        - JSON that was double-encoded as a string
    """

    if text is None:
        raise ValueError("GenAI response was empty.")

    original = text
    text = text.strip().lstrip("\ufeff")

    # Remove Markdown code fences if present.
    text = _FENCE_OPEN.sub("", text)
    text = _FENCE_CLOSE.sub("", text)
    text = text.strip()

    # Fast path: the whole string is JSON.
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    else:
        if isinstance(parsed, dict):
            return parsed

        # Double-encoded JSON: the model returned a JSON *string*
        # that itself contains a JSON object.
        if isinstance(parsed, str) and _depth < 2:
            return extract_json(parsed, _depth + 1)

    # Slow path: find the first decodable JSON object anywhere
    # in the text (handles leading/trailing prose and fences).
    last_error = None

    for match in re.finditer(r"\{", text):
        try:
            candidate, _ = _JSON_DECODER.raw_decode(text, match.start())
        except json.JSONDecodeError as exc:
            last_error = exc
            continue

        if isinstance(candidate, dict):
            return candidate

    if last_error is not None:
        raise ValueError(
            f"GenAI returned malformed JSON:\n{original}"
        ) from last_error

    raise ValueError(
        f"GenAI response did not contain JSON:\n{original}"
    )


# ============================================================
# EXTRACTION VALIDATION
# ============================================================

def validate_extraction(data: dict) -> dict:
    """
    Validate and normalize GenAI emergency extraction.
    """

    required_fields = {
        "emergency_type",
        "affected_people",
        "injuries",
        "critical_indicators",
        "location_information",
    }

    missing = required_fields - data.keys()

    if missing:
        raise ValueError(
            f"Missing GenAI fields: {sorted(missing)}"
        )

    emergency_type = str(
        data["emergency_type"]
    ).lower().strip()

    allowed_types = {
        "accident",
        "fire",
        "flood",
        "other",
    }

    if emergency_type not in allowed_types:
        emergency_type = "other"

    try:
        affected_people = max(
            0,
            int(data["affected_people"]),
        )
    except (TypeError, ValueError):
        affected_people = 0

    try:
        injuries = max(
            0,
            int(data["injuries"]),
        )
    except (TypeError, ValueError):
        injuries = 0

    critical_indicators = data["critical_indicators"]

    if not isinstance(critical_indicators, list):
        critical_indicators = []

    critical_indicators = [
        str(item).strip()
        for item in critical_indicators
        if str(item).strip()
    ]

    location_information = str(
        data["location_information"] or ""
    ).strip()

    return {
        "emergency_type": emergency_type,
        "affected_people": affected_people,
        "injuries": injuries,
        "critical_indicators": critical_indicators,
        "location_information": location_information,
    }


# ============================================================
# EMERGENCY EXTRACTION
# ============================================================

def extract_emergency_information(
    description: str,
) -> dict:
    """
    Extract structured emergency information.

    Pipeline:

        Native Indic Language
                ↓
        Language Detection
                ↓
        IndicTrans2
                ↓
             English
                ↓
              Qwen
                ↓
        Structured JSON

    English input goes directly to Qwen.
    """

    # STEP 1: Detect language and translate if necessary
    prepared = prepare_emergency_text(description)

    english_description = prepared["translated_text"]
    source_language = prepared["source_language"]

    # STEP 2: Load Qwen
    llm = load_model()

    # STEP 3: Build Qwen prompt
    user_prompt = f"""
Emergency report:

{english_description}

Extract the required information and return ONLY valid JSON.
"""

    # STEP 4: Run Qwen
    with MODEL_LOCK:
        response = llm.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": EXTRACTION_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            max_tokens=MAX_NEW_TOKENS,
            temperature=0.0,
            response_format={
                "type": "json_object"
            },
        )

    # STEP 5: Parse Qwen JSON
    content = get_message_content(response)

    parsed = extract_json(content)

    validated = validate_extraction(parsed)

    # STEP 6: Add multilingual metadata
    validated["source_language"] = source_language
    validated["original_text"] = description
    validated["translated_text"] = english_description

    return validated


# ============================================================
# MISSING INFORMATION
# ============================================================

def validate_missing_information(data: dict) -> dict:
    """
    Validate and normalize GenAI missing-information detection.
    """

    required_fields = {
        "known_information",
        "missing_information",
        "urgency",
    }

    missing = required_fields - data.keys()

    if missing:
        raise ValueError(
            f"Missing GenAI fields: {sorted(missing)}"
        )

    known_information = data["known_information"]

    if not isinstance(known_information, list):
        known_information = []

    known_information = [
        str(item).strip()
        for item in known_information
        if str(item).strip()
    ]

    missing_information = data["missing_information"]

    if not isinstance(missing_information, list):
        missing_information = []

    missing_information = [
        str(item).strip()
        for item in missing_information
        if str(item).strip()
    ]

    urgency = str(
        data["urgency"]
    ).lower().strip()

    allowed_urgency = {
        "low",
        "medium",
        "high",
    }

    if urgency not in allowed_urgency:
        urgency = "medium"

    return {
        "known_information": known_information,
        "missing_information": missing_information,
        "urgency": urgency,
    }


def detect_missing_information(
    description: str,
    affected_people: int,
    injuries: int,
    emergency_type: str | None = None,
    location: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    critical_indicators: list[str] | None = None,
) -> dict:
    """
    Use Qwen to identify important information that is
    known and information that is still missing.
    """

    # Translate native-language reports first.
    prepared = prepare_emergency_text(description)

    english_description = prepared["translated_text"]

    llm = load_model()

    critical_indicators = critical_indicators or []

    structured_context = f"""
Emergency type: {emergency_type or "unknown"}
Affected people: {affected_people}
Injuries: {injuries}
Location: {location or "not provided"}
Latitude: {latitude if latitude is not None else "not provided"}
Longitude: {longitude if longitude is not None else "not provided"}
Critical indicators: {
    ", ".join(critical_indicators)
    if critical_indicators
    else "none"
}
"""

    user_prompt = f"""
Emergency report:

{english_description}

Structured incident information already available:

{structured_context}

Analyze ALL of the information above together.

Identify:

1. Important information that is already known.

2. Important information that is genuinely missing and would help
   emergency responders understand, assess, or respond to the incident.

Do NOT list information as missing if it is already available in either
the emergency report or the structured incident information.

Do NOT invent facts or answers for missing information.

Return ONLY valid JSON.
"""

    with MODEL_LOCK:
        response = llm.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": MISSING_INFORMATION_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            max_tokens=MISSING_INFO_MAX_TOKENS,
            temperature=0.0,
            response_format={
                "type": "json_object"
            },
        )

    content = get_message_content(response)

    parsed = extract_json(content)

    return validate_missing_information(parsed)


# ============================================================
# MULTILINGUAL VALIDATION
# ============================================================

def validate_multilingual_emergency(data: dict) -> dict:
    """
    Validate and normalize multilingual emergency understanding.
    """

    required_fields = {
        "detected_language",
        "normalized_report",
        "emergency_type",
        "affected_people",
        "injuries",
        "critical_indicators",
        "location_information",
    }

    missing = required_fields - data.keys()

    if missing:
        raise ValueError(
            f"Missing GenAI fields: {sorted(missing)}"
        )

    detected_language = str(
        data["detected_language"] or ""
    ).strip()

    normalized_report = str(
        data["normalized_report"] or ""
    ).strip()

    emergency_type = str(
        data["emergency_type"]
    ).lower().strip()

    allowed_types = {
        "accident",
        "fire",
        "flood",
        "other",
    }

    if emergency_type not in allowed_types:
        emergency_type = "other"

    try:
        affected_people = max(
            0,
            int(data["affected_people"]),
        )
    except (TypeError, ValueError):
        affected_people = 0

    try:
        injuries = max(
            0,
            int(data["injuries"]),
        )
    except (TypeError, ValueError):
        injuries = 0

    critical_indicators = data["critical_indicators"]

    if not isinstance(critical_indicators, list):
        critical_indicators = []

    critical_indicators = [
        str(item).strip()
        for item in critical_indicators
        if str(item).strip()
    ]

    location_information = str(
        data["location_information"] or ""
    ).strip()

    return {
        "detected_language": detected_language,
        "normalized_report": normalized_report,
        "emergency_type": emergency_type,
        "affected_people": affected_people,
        "injuries": injuries,
        "critical_indicators": critical_indicators,
        "location_information": location_information,
    }


# ============================================================
# LEGACY MULTILINGUAL FUNCTION
# ============================================================

def understand_multilingual_emergency(
    description: str,
) -> dict:
    """
    Existing Qwen-only multilingual understanding function.

    Kept for compatibility.

    The main emergency extraction path now uses:

        Language Detection
        → IndicTrans2
        → English
        → Qwen

    for supported native Indic languages.
    """

    llm = load_model()

    user_prompt = f"""
Emergency report:

{description}

Understand the report regardless of the language or writing style.

Detect the original language, normalize the report into concise
English, and extract the structured emergency information.

Return ONLY valid JSON.
"""

    with MODEL_LOCK:
        response = llm.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": MULTILINGUAL_EMERGENCY_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            max_tokens=MULTILINGUAL_MAX_NEW_TOKENS,
            temperature=0.0,
            response_format={
                "type": "json_object"
            },
        )

    content = get_message_content(response)

    parsed = extract_json(content)

    return validate_multilingual_emergency(parsed)


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    test_description = (
        "Major accident near the highway. "
        "Three people are injured and one person "
        "is unconscious."
    )

    print("\nTesting GenAI extraction...\n")

    result = extract_emergency_information(
        test_description
    )

    print("GenAI Extraction:")

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )

    print("\nTesting Missing Information Detection...\n")

    missing_info = detect_missing_information(
        description=test_description,
        affected_people=3,
        injuries=3,
        emergency_type="accident",
    )

    print("GenAI Missing Information:")

    print(
        json.dumps(
            missing_info,
            indent=2,
        )
    )