"""Provider wiring checked against mocked HTTP endpoints (no real model in CI)."""
import json

import httpx
import pytest

from app.core.config import settings
from app.services import llm_provider


@pytest.fixture
def capture(monkeypatch):
    seen = {}
    real = httpx.Client

    def handler(request: httpx.Request):
        seen["url"] = str(request.url)
        seen["headers"] = dict(request.headers)
        seen["body"] = json.loads(request.content or b"{}")
        if "/api/chat" in seen["url"]:
            return httpx.Response(200, json={"message": {"content": '<think></think>{"category": "fire"}'}})
        if "generateContent" in seen["url"]:
            return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": '{"category":"flood"}'}]}}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": '```json\n{"category":"medical"}\n```'}}]})

    monkeypatch.setattr(httpx, "Client", lambda **kw: real(transport=httpx.MockTransport(handler), **{k: v for k, v in kw.items() if k != "transport"}))
    return seen


def test_ollama_disables_thinking_and_forces_json(capture, monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    r = llm_provider.complete_json("sys", "user")
    assert r.ok and r.data == {"category": "fire"}
    assert capture["body"]["think"] is False and capture["body"]["format"] == "json"
    assert capture["body"]["keep_alive"] == settings.OLLAMA_KEEP_ALIVE and capture["body"]["stream"] is False


def test_gemini_json_mode_and_no_thinking_budget(capture, monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "k")
    r = llm_provider.complete_json("sys", "user")
    assert r.ok and r.data == {"category": "flood"}
    cfg = capture["body"]["generationConfig"]
    assert cfg["responseMimeType"] == "application/json" and cfg["thinkingConfig"]["thinkingBudget"] == 0
    assert capture["headers"]["x-goog-api-key"] == "k"  # key in header, not URL


def test_openai_compatible_parses_fenced_json(capture, monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")
    r = llm_provider.complete_json("sys", "user")
    assert r.ok and r.data == {"category": "medical"}
    assert capture["body"]["response_format"] == {"type": "json_object"}


def test_vision_sends_image(capture, monkeypatch):
    monkeypatch.setattr(settings, "VISION_PROVIDER", "ollama")
    llm_provider.analyze_image_json("sys", "u", llm_provider.Attachment("image/jpeg", b"\xff\xd8abc"))
    assert capture["body"]["messages"][1]["images"] and capture["body"]["model"] == settings.OLLAMA_VISION_MODEL


def test_unreachable_provider_is_a_clean_failure(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:9")
    r = llm_provider.complete_json("sys", "user", timeout=2)
    assert not r.ok and r.error and r.latency_ms is not None
