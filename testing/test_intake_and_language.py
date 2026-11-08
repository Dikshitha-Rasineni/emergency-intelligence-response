"""Citizen intake, tracking, multilingual handling, extraction rules, LLM validation."""
import re
import pytest

from app.services import llm_provider
from app.services.ai_service import AIService
from app.services.language_service import LanguageService

INDIC = re.compile(r"[ऀ-෿]")


def test_health_reports_real_state(client):
    d = client.get("/api/v1/health").json()
    assert d["database"] == "connected"
    assert d["postgis"] != "missing"
    assert d["ai"]["text"]["status"] == "disabled"


def test_login_rejects_bad_password(client):
    r = client.post("/api/v1/auth/login", json={"email": "admin@resq.demo", "password": "wrong"})
    assert r.status_code == 401


def test_report_returns_token_and_rule_assessment(client, report, unique_point):
    lat, lng = unique_point()
    d = report("Three people injured and one person is unconscious after a crash on the highway", lat, lng,
               user_priority=1)
    v = d["citizen_view"]
    assert d["tracking_token"] and len(d["tracking_token"]) > 20
    assert v["category"] == "road_accident"
    assert v["assessment"]["priority_score"] >= 75  # user_priority=1 must be ignored
    assert "unconscious" in v["assessment"]["evidence_codes"]
    assert v["location"]["verified"] is True


def test_tracking_requires_token(client, report):
    d = report("Smoke coming from a shop, no one inside")
    iid = d["incident_id"]
    assert client.get(f"/api/v1/incidents/{iid}/track").status_code == 403
    assert client.get(f"/api/v1/incidents/{iid}/track", headers={"X-Tracking-Token": "x" * 30}).status_code == 403
    ok = client.get(f"/api/v1/incidents/{iid}/track", headers={"X-Tracking-Token": d["tracking_token"]})
    assert ok.status_code == 200


def test_location_unverified_when_missing(client, report):
    v = report("Someone fainted at the bus stand")["citizen_view"]
    assert v["location"]["verified"] is False
    assert "Location not verified" in v["uncertainties"]


def test_no_confirmed_emergency_is_not_safe(client, report):
    v = report("hello is this working")["citizen_view"]
    assert v["assessment"]["insufficient_evidence"] is True
    assert v["category"] == "other"


@pytest.mark.parametrize("text,lang,category", [
    ("రోడ్డు ప్రమాదం జరిగింది, ఇద్దరు గాయపడ్డారు", "te", "road_accident"),          # 10 Telugu
    ("தீ விபத்து, கட்டிடத்தில் புகை வருகிறது", "ta", "fire"),                         # 11 Tamil
    ("सड़क दुर्घटना हुई है, दो लोग घायल हैं", "hi", "road_accident"),                  # 12 Hindi
    ("Accident at the flyover, one person hurt", "en", "road_accident"),             # 13 English
])
def test_multilingual_user_language_and_english_control_room(client, report, auth, unique_point, text, lang, category):
    lat, lng = unique_point()
    d = report(text, lat, lng)
    v = d["citizen_view"]
    assert v["language"]["detected"] == lang
    assert v["guidance"]["language"] == lang                 # citizen gets their language
    assert v["category"] == category
    full = client.get(f"/api/v1/control-room/incidents/{d['incident_id']}", headers=auth["ADMIN"]).json()
    assert full["english_summary"] and not INDIC.search(full["english_summary"])  # control room English
    for dep in [r["department"] for r in full["routing"] if r["included"]]:
        view = client.get(f"/api/v1/control-room/incidents/{d['incident_id']}", headers=auth[dep]).json()
        assert "original_text" not in view
        assert not INDIC.search(str(view.get("brief")))


def test_code_switched_and_transliterated():
    mixed = LanguageService.detect("Bike accident ayyindi, ఇద్దరు గాయపడ్డారు please help")
    assert mixed["language"] == "te" and mixed["mixed"] is True                      # 14
    tr = LanguageService.detect("bike pramadam jarigindi kapadandi")
    assert tr["language"] == "te" and tr["transliterated"] and tr["confidence"] <= 0.6  # 16
    assert AIService.extract("bike pramadam jarigindi kapadandi", "te", use_llm=False).category == "road_accident"


def test_uncertain_language_low_confidence():                                        # 17
    d = LanguageService.detect("ok")
    assert d["confidence"] <= 0.6


def test_preferred_language_overrides_detected(client, report):
    v = report("Fire in the godown behind the market", preferred_language="hi")["citizen_view"]
    assert v["guidance"]["language"] == "hi"


def test_unsupported_language_falls_back_to_english_guidance(client, report):
    v = report("ಬೆಂಕಿ ಹೊತ್ತಿದೆ, ಹೊಗೆ ತುಂಬಿದೆ")["citizen_view"]  # Kannada: detection yes, guidance not translated yet
    assert v["language"]["detected"] == "kn"
    assert v["guidance"]["language"] == "en" and v["guidance"]["language_fallback"] is True


@pytest.mark.parametrize("text,inj,cert", [
    ("Small kitchen fire, nobody is hurt", 0, "denied"),
    ("one person might be injured near the bus stop", 1, "possible"),
    ("2 people injured in the collision", 2, "confirmed"),
    ("Flood water entering houses", 0, "none_reported"),
])
def test_negation_and_uncertainty_preserved(text, inj, cert):
    e = AIService.extract(text, "en", use_llm=False)
    assert (e.injuries, e.injury_certainty) == (inj, cert)


def test_llm_hallucinated_numbers_are_rejected(monkeypatch):
    def fake(system, user, timeout=None):
        return llm_provider.LLMResult(ok=True, provider="test", model="fake", latency_ms=5, text="{}", data={
            "category": "road_accident", "injuries_reported": 7, "injury_certainty": "confirmed",
            "affected_people": 40, "hazards": ["fire", "made_up"], "needs": ["medical"], "trapped": False,
            "unconscious_or_not_breathing": False, "english_summary": "Crash with 7 injured.",
            "uncertainties": [], "missing_information": []})
    monkeypatch.setattr(llm_provider, "complete_json", fake)
    e = AIService.extract("Bike crash on the main road, one person injured", "en")
    assert e.method == "llm"
    assert e.injuries == 1 and e.affected_people == 1       # 7 and 40 do not appear in the text
    assert "made_up" not in e.hazards
    assert any("does not appear" in n for n in e.validation_notes)


def test_llm_failure_falls_back(monkeypatch):                                         # 18 / AI unavailable
    monkeypatch.setattr(llm_provider, "complete_json",
                        lambda *a, **k: llm_provider.LLMResult(ok=False, provider="ollama", error="timeout"))
    e = AIService.extract("Fire in the parking lot", "en")
    assert e.method == "rule_based" and e.category == "fire"


def test_background_llm_enrichment_updates_record(client, report, auth, monkeypatch, unique_point):
    monkeypatch.setattr(llm_provider, "complete_json", lambda *a, **k: llm_provider.LLMResult(
        ok=True, provider="test", model="fake", latency_ms=3, text="{}", data={
            "category": "fire", "injuries_reported": None, "injury_certainty": "none_reported", "affected_people": None,
            "hazards": ["smoke"], "needs": [], "trapped": True, "unconscious_or_not_breathing": False,
            "english_summary": "Smoke from the second-floor kitchen; two people are trapped inside.",
            "uncertainties": [], "missing_information": []}))
    lat, lng = unique_point()
    d = report("రెండవ అంతస్తులో వంటగది నుండి పొగ వస్తోంది, ఇద్దరు లోపల చిక్కుకున్నారు", lat, lng)
    full = client.get(f"/api/v1/control-room/incidents/{d['incident_id']}", headers=auth["ADMIN"]).json()
    assert full["ai"]["method"] == "llm" and full["ai"]["status"] == "COMPLETED"
    assert full["english_summary"].startswith("Smoke from the second-floor")
    assert full["trapped"] is True
    fire = next(r for r in full["routing"] if r["department"] == "FIRE")
    assert fire["included"] and fire["role"] == "PRIMARY"
