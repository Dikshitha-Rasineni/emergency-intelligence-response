import json
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

from .language import detect_language


TRANSLATOR_URL = "http://127.0.0.1:8001/translate"


SUPPORTED_LANGUAGES = {
    "Tamil",
    "Telugu",
    "Kannada",
    "Malayalam",
    "Hindi",
}


def _call_translator_service(payload: dict) -> str:
    """
    POST a payload to the local IndicTrans2 service and
    return the translated_text field.
    """

    request = Request(
        TRANSLATOR_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(
            request,
            timeout=120,
        ) as response:

            body = response.read().decode("utf-8")

            result = json.loads(body)

            translated_text = result.get(
                "translated_text"
            )

            if not translated_text:
                raise RuntimeError(
                    "Translator service returned no translated_text"
                )

            return translated_text

    except HTTPError as exc:
        error_body = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"Translator service HTTP {exc.code}: "
            f"{error_body}"
        ) from exc

    except URLError as exc:
        raise RuntimeError(
            "IndicTrans2 translator service is not running "
            "on http://127.0.0.1:8001"
        ) from exc


def translate_to_english(
    text: str,
    source_language: str,
) -> str:

    if not text or not text.strip():
        return ""

    if not source_language:
        return text

    if source_language.lower() == "english":
        return text

    if source_language not in SUPPORTED_LANGUAGES:
        return text

    return _call_translator_service(
        {
            "text": text,
            "source_language": source_language,
        }
    )


def translate_from_english(
    text: str,
    target_language: str,
) -> str:
    """
    Translate English text into a supported native Indic language.

    Requires the translator service to support the English -> Indic
    direction. If the service returns text that is not in the target
    script (e.g. it ignored the request and echoed English), a
    RuntimeError is raised rather than returning a fake translation.
    """

    if not text or not text.strip():
        return text

    if not target_language:
        return text

    if target_language.lower() == "english":
        return text

    if target_language not in SUPPORTED_LANGUAGES:
        return text

    translated = _call_translator_service(
        {
            "text": text,
            "source_language": "English",
            "target_language": target_language,
            "direction": "en_to_indic",
        }
    )

    if detect_language(translated) != target_language:
        raise RuntimeError(
            "Translator service did not return "
            f"{target_language} text. It may not support "
            "English -> Indic translation."
        )

    return translated