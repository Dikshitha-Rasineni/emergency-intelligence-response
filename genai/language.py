import re


def detect_language(text: str) -> str:
    """
    Lightweight script-based language detection.

    This detects native Indic scripts.
    Romanized Indic languages are intentionally not classified
    as Tamil/Telugu/Kannada/Malayalam/Hindi.
    """

    if not text or not text.strip():
        return "English"

    # Tamil
    if re.search(r"[\u0B80-\u0BFF]", text):
        return "Tamil"

    # Telugu
    if re.search(r"[\u0C00-\u0C7F]", text):
        return "Telugu"

    # Kannada
    if re.search(r"[\u0C80-\u0CFF]", text):
        return "Kannada"

    # Malayalam
    if re.search(r"[\u0D00-\u0D7F]", text):
        return "Malayalam"

    # Devanagari
    if re.search(r"[\u0900-\u097F]", text):
        return "Hindi"

    return "English"