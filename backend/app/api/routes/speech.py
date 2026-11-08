from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.core.config import settings
from app.core.rate_limit import check_rate
from app.services import llm_provider
from app.services.language_service import LanguageService

router = APIRouter()
ALLOWED = ("audio/webm", "audio/ogg", "audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp4", "audio/aac")


@router.post("/speech/transcribe")
async def transcribe(request: Request, audio: UploadFile = File(...), language: Optional[str] = Form(None)):
    """Server-side speech-to-text (used when the browser has no speech recognition for the language).
    Audio is transcribed in memory and not stored. The citizen reviews and edits the text before submitting."""
    check_rate(request, "stt", 10)
    if settings.STT_PROVIDER.lower() == "none":
        raise HTTPException(503, detail={"error": "STT_DISABLED", "message": "Server speech recognition is not configured."})
    mime = (audio.content_type or "").split(";")[0]
    if mime not in ALLOWED:
        raise HTTPException(415, detail={"error": "UNSUPPORTED_AUDIO", "message": f"Unsupported audio type {mime}."})
    raw = await audio.read(int(settings.MAX_AUDIO_MB * 1024 * 1024) + 1)
    if len(raw) > settings.MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(413, detail={"error": "TOO_LARGE"})
    r = llm_provider.transcribe_audio(llm_provider.Attachment(mime, raw), language if language != "auto" else None)
    if not r.ok:
        raise HTTPException(502, detail={"error": "STT_FAILED", "message": "Transcription failed. Please type your report."})
    text = (r.data or {}).get("text") or r.text
    det = LanguageService.detect(text)
    return {"text": text, "language": det["language"], "language_confidence": det["confidence"],
            "provider": r.provider, "latency_ms": r.latency_ms,
            "notice": "Check the text before sending. Background noise can cause errors."}
