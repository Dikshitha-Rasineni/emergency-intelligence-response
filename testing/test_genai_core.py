"""GenAI core: incident briefs, RAG citizen guidance and Ask RESQ, with grounding checks and fallbacks."""
import random

import pytest

from app.services import genai_service, translation_service
from app.services.llm_provider import LLMResult

DEV = {"Authorization": "Bearer test-device-token"}


def crash(client, g=6.4):
    lat, lng = 12.86 + random.random() * 0.15, 80.06 + random.random() * 0.15
    r = client.post("/api/v1/iot/events", headers=DEV, json={
        "device_id": "GENAI-CAR", "event_id": f"GENAI:{random.random()}", "event_type": "ACCIDENT", "alert_qualified": True,
        "latitude": lat, "longitude": lng, "acceleration_magnitude_g": g, "reason": "Severe vehicle impact detected",
        "observed_value": g, "threshold_value": 3.5, "measurement_unit": "g"})
    assert r.status_code == 201, r.text
    return r.json()["incident_id"]


class FakeLLM:
    def __init__(self, data):
        self.data, self.calls = data, []

    def __call__(self, system, user, timeout=None, **kw):
        self.calls.append((system, user))
        d = self.data(system, user) if callable(self.data) else self.data
        return LLMResult(ok=d is not None, data=d, text="{}", provider="fake", model="qwen-test", latency_ms=5,
                         error=None if d is not None else "offline")


def test_sensor_incident_gets_grounded_genai_brief(client, auth, monkeypatch):
    fake = FakeLLM({"headline": "Car hit a pole at 6.4 g on GST Road",
                    "situation": "An in-car sensor recorded a 6.4 g impact. No person has confirmed it yet.",
                    "actions": ["Treat the driver as a possible spinal injury.", "Send 7 ambulances immediately.",
                                "Prepare the trauma bay."],
                    "prepare": ["Spinal board and collar"], "risks": ["Driver may be unconscious"],
                    "confirm": ["Is the driver breathing?"], "citations": ["G1", "G9"]})
    monkeypatch.setattr(genai_service.llm_provider, "complete_json", fake)
    iid = crash(client)
    b = client.get(f"/api/v1/control-room/incidents/{iid}/genai-brief", headers=auth["HOSPITAL"]).json()
    assert b["generated"] is True and b["model"] == "fake:qwen-test"
    assert "Send 7 ambulances immediately." not in b["actions"]  # invented number removed by the grounding check
    assert any("unsupported number" in c for c in b["checks"]) and b["grounding"] == "partial"
    assert "6.4" in b["headline"] and b["actions"][0].startswith("Treat")
    assert [c["id"] for c in b["citations"]] == ["G1"] and b["citations"][0]["excerpt"]  # G9 was never retrieved
    # prompt carried the sensor facts and retrieved guidance, and treated text as data
    system, user = fake.calls[-1]
    assert "never instructions" in system and "<facts>" in user and "6.4" in user and "[G1]" in user
    # cached: opening the incident returns it without another model call
    n = len(fake.calls)
    v = client.get(f"/api/v1/control-room/incidents/{iid}", headers=auth["HOSPITAL"]).json()
    assert v["genai_brief"]["headline"] == b["headline"] and len(fake.calls) == n
    # each service gets its own brief
    p = client.get(f"/api/v1/control-room/incidents/{iid}/genai-brief", headers=auth["POLICE"]).json()
    assert p["department"] == "POLICE"


def test_brief_falls_back_to_rules_when_genai_offline(client, auth, monkeypatch):
    monkeypatch.setattr(genai_service.llm_provider, "complete_json", FakeLLM(None))
    iid = crash(client, 5.1)
    b = client.get(f"/api/v1/control-room/incidents/{iid}/genai-brief?refresh=true", headers=auth["HOSPITAL"]).json()
    assert b["generated"] is False and b["grounding"] == "fallback" and b["actions"]
    assert any("GenAI unavailable" in c for c in b["checks"])


def test_ask_resq_answers_from_record_and_refuses_invented_facts(client, auth, monkeypatch):
    def answer(system, user):
        if "Ask RESQ" not in system:
            return None
        if "how many" in user.lower():
            return {"answer": "There are 4 casualties.", "grounded": True, "citations": []}
        return {"answer": "The sensor read 6.4 g against a 3.5 g limit.", "grounded": True, "citations": ["G1"]}
    monkeypatch.setattr(genai_service.llm_provider, "complete_json", FakeLLM(answer))
    iid = crash(client)
    ok = client.post(f"/api/v1/control-room/incidents/{iid}/ask", json={"question": "What did the sensor read?"},
                     headers=auth["HOSPITAL"]).json()
    assert "6.4" in ok["answer"] and ok["grounded"] is True
    bad = client.post(f"/api/v1/control-room/incidents/{iid}/ask", json={"question": "How many casualties?"},
                      headers=auth["HOSPITAL"]).json()
    assert bad["grounded"] is False and "can't confirm" in bad["answer"]
    # routed-elsewhere rules still apply
    assert client.post(f"/api/v1/control-room/incidents/{iid}/ask", json={"question": "x?"},
                       headers=auth["DISASTER"]).status_code == 404


def test_citizen_gets_rag_guidance_in_their_language(client, report, monkeypatch):
    fake = FakeLLM(lambda s, u: {"steps": ["Do not move the injured person unless there is fire.", "Press on heavy bleeding with a clean cloth."],
                                 "avoid": ["Do not give food or water."], "citations": ["G1"]} if "safety assistant" in s else None)
    monkeypatch.setattr(genai_service.llm_provider, "complete_json", fake)
    monkeypatch.setattr(translation_service, "translate", lambda t, s, d: (f"[{d}] {t}", "test MT"))
    d = report("Car hit a bike near the signal, one man is bleeding", 13.0 + random.random() * 0.1, 80.2 + random.random() * 0.05, preferred_language="te")
    g = client.get(f"/api/v1/incidents/{d['incident_id']}/genai-guidance", headers={"X-Tracking-Token": d["tracking_token"]}).json()
    assert g["generated"] is True and g["language"] == "te" and g["steps"][0].startswith("[te] Do not move")
    assert g["english_steps"][0].startswith("Do not move") and g["citations"][0]["publisher"]
    assert client.get(f"/api/v1/incidents/{d['incident_id']}/genai-guidance").status_code in (401, 403)


def test_llm_translation_must_be_in_the_target_script():
    assert translation_service._script_ok("A car hit a bike near the signal.", "en")
    assert not translation_service._script_ok("సిగ్నల్ దగ్గర కారు బైక్‌ను ఢీకొంది", "en")
    assert translation_service._script_ok("సిగ్నల్ దగ్గర కారు", "te")


def test_sim800l_endpoint_creates_incident_from_force_sensor(client, auth, monkeypatch):
    monkeypatch.setattr(genai_service.llm_provider, "complete_json", FakeLLM(None))
    lat, lng = 12.70 + random.random() * 0.05, 79.90 + random.random() * 0.05
    form = {"id": "SIM-CAR-1", "e": f"SIM-CAR-1:{random.random()}", "ty": "crash", "f": "63.5", "t": "40",
            "raw": "3410", "lat": str(lat), "lng": str(lng), "csq": "17", "fw": "car-1.0", "k": "test-device-token"}
    r = client.post("/api/v1/iot/sim", data=form)
    assert r.status_code == 201 and r.text.startswith("OK ")
    _, reading, incident, status = r.text.split()
    assert incident != "-" and status == "INCIDENT_CREATED"
    v = client.get(f"/api/v1/control-room/incidents/{incident}", headers=auth["HOSPITAL"]).json()
    s = v["sensor_evidence"][0]
    assert s["observed_value"] == 63.5 and s["unit"] == "N" and s["threshold_value"] == 40
    assert v["severity"] in ("HIGH", "CRITICAL")
    # same event id again = duplicate, no second incident; heartbeat never creates one; bad token rejected
    assert client.post("/api/v1/iot/sim", data=form).text.split()[-1] == "DUPLICATE"
    hb = client.post("/api/v1/iot/sim", data={"id": "SIM-CAR-1", "ty": "hb", "raw": "120", "csq": "19", "k": "test-device-token"})
    assert hb.status_code == 201 and hb.text.split()[2] == "-"
    assert client.post("/api/v1/iot/sim", data={**form, "k": "wrong"}).status_code == 401
    devs = client.get("/api/v1/iot/devices", headers=auth["HOSPITAL"]).json()
    car = next(d for d in devs if d["device_id"] == "SIM-CAR-1")
    assert car["transport"] == "GPRS" and car["signal_quality"] == 19
