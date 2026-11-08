"""
Pluggable LLM / vision / speech providers.

Every call returns an LLMResult and never raises: callers decide what to do when
`ok` is False (the incident pipeline always has a rule-based fallback).

Providers
- ollama : local Ollama server. `think: False` disables Qwen3 reasoning (the main
           source of latency), `format: "json"` forces valid JSON, `keep_alive`
           keeps the model loaded between requests.
- gemini : Google Gemini REST API (text, images, audio). thinkingBudget=0 for speed.
- openai : any OpenAI-compatible /chat/completions server (Groq, OpenRouter,
           llama.cpp `llama-server`, vLLM, LM Studio).
- none   : disabled; always returns ok=False.
"""
from __future__ import annotations

import base64
import json
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.logging import logger


@dataclass
class LLMResult:
    ok: bool
    text: str = ""
    data: Optional[Dict[str, Any]] = None
    provider: str = "none"
    model: Optional[str] = None
    latency_ms: Optional[int] = None
    error: Optional[str] = None


@dataclass
class Attachment:
    mime_type: str
    data: bytes = field(repr=False)


def parse_json_object(text: str) -> Optional[Dict[str, Any]]:
    """Extract the first JSON object from model output (tolerates code fences / think tags)."""
    if not text:
        return None
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group(0))
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None
    return None


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------

def _ollama(system: str, user: str, model: str, timeout: float, attachments: List[Attachment]) -> LLMResult:
    msg: Dict[str, Any] = {"role": "user", "content": user}
    images = [base64.b64encode(a.data).decode() for a in attachments if a.mime_type.startswith("image/")]
    if images:
        msg["images"] = images
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}, msg],
        "stream": False,
        "think": False,
        "format": "json",
        "keep_alive": settings.OLLAMA_KEEP_ALIVE,
        "options": {"temperature": 0.1, "num_predict": getattr(_opts, "max_tokens", None) or 900,
                    "num_ctx": settings.OLLAMA_NUM_CTX},
    }
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    with httpx.Client(timeout=timeout) as client:
        res = client.post(url, json=payload)
        if res.status_code == 400 and "think" in res.text.lower():
            # Older Ollama or a model without a thinking switch: retry without the flag.
            payload.pop("think", None)
            res = client.post(url, json=payload)
    res.raise_for_status()
    text = res.json().get("message", {}).get("content", "")
    return LLMResult(ok=True, text=text, provider="ollama", model=model)


def _gemini(system: str, user: str, model: str, timeout: float, attachments: List[Attachment],
            json_mode: bool = True) -> LLMResult:
    if not settings.GEMINI_API_KEY:
        return LLMResult(ok=False, provider="gemini", model=model, error="GEMINI_API_KEY not set")
    parts: List[Dict[str, Any]] = [{"text": user}]
    for a in attachments:
        parts.append({"inline_data": {"mime_type": a.mime_type, "data": base64.b64encode(a.data).decode()}})
    gen_cfg: Dict[str, Any] = {"temperature": 0.1, "maxOutputTokens": 1024}
    if json_mode:
        gen_cfg["responseMimeType"] = "application/json"
    if "2.5" in model and "pro" not in model:
        gen_cfg["thinkingConfig"] = {"thinkingBudget": 0}
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": gen_cfg,
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    with httpx.Client(timeout=timeout) as client:
        res = client.post(url, json=body, headers={"x-goog-api-key": settings.GEMINI_API_KEY})
    res.raise_for_status()
    data = res.json()
    cands = data.get("candidates") or []
    if not cands:
        return LLMResult(ok=False, provider="gemini", model=model,
                         error=f"no candidates (blocked?): {data.get('promptFeedback')}")
    text = "".join(p.get("text", "") for p in cands[0].get("content", {}).get("parts", []))
    return LLMResult(ok=True, text=text, provider="gemini", model=model)


def _openai(system: str, user: str, model: str, timeout: float, attachments: List[Attachment]) -> LLMResult:
    if not model:
        return LLMResult(ok=False, provider="openai", error="model not configured")
    content: Any = user
    images = [a for a in attachments if a.mime_type.startswith("image/")]
    if images:
        content = [{"type": "text", "text": user}] + [
            {"type": "image_url",
             "image_url": {"url": f"data:{a.mime_type};base64,{base64.b64encode(a.data).decode()}"}}
            for a in images
        ]
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}],
        "temperature": 0.1,
        "max_tokens": 800,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"} if settings.OPENAI_API_KEY else {}
    url = f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions"
    with httpx.Client(timeout=timeout) as client:
        res = client.post(url, json=body, headers=headers)
    res.raise_for_status()
    text = res.json()["choices"][0]["message"]["content"] or ""
    return LLMResult(ok=True, text=text, provider="openai", model=model)


def _dispatch(provider: str, model: str, system: str, user: str, timeout: float,
              attachments: List[Attachment]) -> LLMResult:
    provider = (provider or "none").lower()
    start = time.perf_counter()
    try:
        if provider == "ollama":
            result = _ollama(system, user, model, timeout, attachments)
        elif provider == "gemini":
            result = _gemini(system, user, model, timeout, attachments)
        elif provider == "openai":
            result = _openai(system, user, model, timeout, attachments)
        else:
            return LLMResult(ok=False, provider="none", error="provider disabled")
    except httpx.TimeoutException:
        result = LLMResult(ok=False, provider=provider, model=model, error=f"timeout after {timeout}s")
    except httpx.HTTPStatusError as e:
        result = LLMResult(ok=False, provider=provider, model=model,
                           error=f"HTTP {e.response.status_code}: {e.response.text[:200]}")
    except Exception as e:  # connection refused, DNS, bad JSON ...
        result = LLMResult(ok=False, provider=provider, model=model, error=f"{type(e).__name__}: {e}")
    result.latency_ms = int((time.perf_counter() - start) * 1000)
    if result.ok:
        result.data = parse_json_object(result.text)
        if result.data is None:
            result.ok = False
            result.error = "model did not return a JSON object"
    log = logger.info if result.ok else logger.warning
    log(f"llm provider={provider} model={model} ok={result.ok} latency_ms={result.latency_ms}"
        + (f" error={result.error}" if result.error else ""))
    return result


def text_model() -> tuple[str, str]:
    p = settings.LLM_PROVIDER.lower()
    return p, {"ollama": settings.OLLAMA_MODEL, "gemini": settings.GEMINI_MODEL,
               "openai": settings.OPENAI_MODEL}.get(p, "")


def vision_model() -> tuple[str, str]:
    p = settings.VISION_PROVIDER.lower()
    return p, {"ollama": settings.OLLAMA_VISION_MODEL, "gemini": settings.GEMINI_VISION_MODEL,
               "openai": settings.OPENAI_VISION_MODEL}.get(p, "")


_opts = threading.local()


def complete_json(system: str, user: str, timeout: Optional[float] = None, max_tokens: Optional[int] = None,
                  fast: bool = False) -> LLMResult:
    """fast=True uses GENAI_FAST_MODEL (e.g. qwen3:1.7b) when configured: for the short GenAI briefs."""
    provider, model = text_model()
    if fast and settings.GENAI_FAST_MODEL and provider == "ollama":
        model = settings.GENAI_FAST_MODEL
    _opts.max_tokens = max_tokens
    try:
        return _dispatch(provider, model, system, user, timeout or settings.LLM_TIMEOUT_SECONDS, [])
    finally:
        _opts.max_tokens = None


def analyze_image_json(system: str, user: str, image: Attachment, timeout: Optional[float] = None) -> LLMResult:
    provider, model = vision_model()
    return _dispatch(provider, model, system, user, timeout or settings.VISION_TIMEOUT_SECONDS, [image])


def transcribe_audio(audio: Attachment, language_hint: Optional[str] = None) -> LLMResult:
    """Server-side speech-to-text. Returns data={"text": ..., "language": ...}."""
    provider = settings.STT_PROVIDER.lower()
    start = time.perf_counter()
    try:
        if provider == "gemini":
            system = ("You transcribe emergency voice reports verbatim. Do not translate or summarise. "
                      "Return JSON: {\"text\": str, \"language\": ISO-639-1 code}.")
            hint = f" Expected language: {language_hint}." if language_hint else ""
            r = _gemini(system, "Transcribe this audio exactly." + hint, settings.GEMINI_MODEL,
                        settings.LLM_TIMEOUT_SECONDS * 2, [audio])
            r.latency_ms = int((time.perf_counter() - start) * 1000)
            if r.ok:
                r.data = parse_json_object(r.text)
                r.ok = bool(r.data and isinstance(r.data.get("text"), str))
            return r
        if provider == "openai":
            ext = {"audio/webm": "webm", "audio/ogg": "ogg", "audio/wav": "wav", "audio/mpeg": "mp3",
                   "audio/mp4": "m4a"}.get(audio.mime_type.split(";")[0], "webm")
            files = {"file": (f"report.{ext}", audio.data, audio.mime_type)}
            form = {"model": settings.OPENAI_STT_MODEL, "response_format": "json"}
            if language_hint:
                form["language"] = language_hint
            headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"} if settings.OPENAI_API_KEY else {}
            with httpx.Client(timeout=60) as client:
                res = client.post(f"{settings.OPENAI_BASE_URL.rstrip('/')}/audio/transcriptions",
                                  data=form, files=files, headers=headers)
            res.raise_for_status()
            text = res.json().get("text", "")
            return LLMResult(ok=bool(text), text=text, data={"text": text, "language": language_hint},
                             provider="openai", model=settings.OPENAI_STT_MODEL,
                             latency_ms=int((time.perf_counter() - start) * 1000))
    except Exception as e:
        return LLMResult(ok=False, provider=provider, error=f"{type(e).__name__}: {e}",
                         latency_ms=int((time.perf_counter() - start) * 1000))
    return LLMResult(ok=False, provider="none", error="speech-to-text provider disabled")


def provider_status() -> Dict[str, Any]:
    """Cheap reachability probe for /health (no generation)."""
    out: Dict[str, Any] = {}
    for kind, (prov, model) in (("text", text_model()), ("vision", vision_model())):
        status = "disabled"
        if prov == "ollama":
            try:
                with httpx.Client(timeout=1.5) as c:
                    tags = c.get(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags").json().get("models", [])
                names = {t.get("name") for t in tags} | {t.get("model") for t in tags}
                status = "ready" if model in names or f"{model}:latest" in names else "model_not_pulled"
            except Exception:
                status = "unreachable"
        elif prov == "gemini":
            status = "configured" if settings.GEMINI_API_KEY else "missing_api_key"
        elif prov == "openai":
            status = "configured" if model else "missing_model"
        out[kind] = {"provider": prov, "model": model or None, "status": status}
    out["speech"] = {"provider": settings.STT_PROVIDER, "status": "configured" if settings.STT_PROVIDER != "none" else "disabled"}
    return out
