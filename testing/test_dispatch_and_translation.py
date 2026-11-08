"""Unit dispatch (auto + manual + crew phone) and machine translation of non-English reports."""
import random

import pytest

DEV = {"Authorization": "Bearer test-device-token"}


def chennai():
    return 12.86 + random.random() * 0.18, 80.06 + random.random() * 0.18


def view(client, auth, role, iid):
    r = client.get(f"/api/v1/control-room/incidents/{iid}", headers=auth[role])
    assert r.status_code == 200, r.text
    return r.json()


def finish(client, auth, v):
    """Release units so later tests find them available."""
    for d in v.get("dispatches", []):
        if d["status"] in ("ASSIGNED", "EN_ROUTE"):
            client.post(f"/api/v1/control-room/dispatches/{d['id']}/status", json={"status": "CANCELLED"}, headers=auth["ADMIN"])


def test_sensor_crash_auto_dispatches_ambulance_and_patrol(client, auth):
    lat, lng = chennai()
    r = client.post("/api/v1/iot/events", headers=DEV, json={
        "device_id": "DEV-AUTO", "event_id": f"DEV-AUTO:{random.random()}", "event_type": "ACCIDENT", "alert_qualified": True,
        "latitude": lat, "longitude": lng, "acceleration_magnitude_g": 4.2, "reason": "impact"}).json()
    v = view(client, auth, "HOSPITAL", r["incident_id"])
    by = {d["department"]: d for d in v["dispatches"]}
    assert by["HOSPITAL"]["unit"]["unit_type"] == "AMBULANCE" and by["HOSPITAL"]["auto"] is True
    assert "POLICE" in by and by["HOSPITAL"]["eta_min"] > 0 and by["HOSPITAL"]["destination"]["name"]
    assert by["HOSPITAL"]["eta_source"] in ("ROAD_ROUTE", "STRAIGHT_LINE_ESTIMATE")
    assert client.get(f"/api/v1/incidents/{r['incident_id']}/track").status_code in (401, 403)  # no citizen token
    finish(client, auth, v)


def test_low_priority_report_is_not_auto_dispatched_but_can_be(client, auth, report):
    lat, lng = chennai()
    d = report("Small dustbin fire outside the shop, no one hurt", lat, lng)
    v = view(client, auth, "FIRE", d["incident_id"])
    assert v["severity"] in ("LOW", "MODERATE") and v["dispatches"] == []
    cands = client.get(f"/api/v1/control-room/incidents/{d['incident_id']}/units", headers=auth["FIRE"]).json()
    assert cands and all(c["department"] == "FIRE" for c in cands)
    assert cands == sorted(cands, key=lambda c: (not (c["preferred_type"] and c["eta_min"] <= cands[0]["eta_min"] + 5), c["eta_min"])) or cands[0]["preferred_type"]
    # another service cannot send fire units
    assert client.post(f"/api/v1/control-room/incidents/{d['incident_id']}/dispatch", json={"unit_id": cands[0]["id"]},
                       headers=auth["POLICE"]).status_code in (403, 404)
    disp = client.post(f"/api/v1/control-room/incidents/{d['incident_id']}/dispatch", json={"unit_id": cands[0]["id"]},
                       headers=auth["FIRE"]).json()
    assert disp["status"] == "ASSIGNED" and disp["auto"] is False
    # busy unit cannot be double-booked
    assert client.post(f"/api/v1/control-room/incidents/{d['incident_id']}/dispatch", json={"unit_id": cands[0]["id"]},
                       headers=auth["FIRE"]).status_code == 409
    for s in ("EN_ROUTE", "ON_SCENE", "COMPLETED"):
        r = client.post(f"/api/v1/control-room/dispatches/{disp['id']}/status", json={"status": s}, headers=auth["FIRE"])
        assert r.status_code == 200, r.text
    assert client.post(f"/api/v1/control-room/dispatches/{disp['id']}/status", json={"status": "EN_ROUTE"},
                       headers=auth["FIRE"]).status_code == 409  # no going backwards
    units = client.get("/api/v1/control-room/units", headers=auth["FIRE"]).json()
    assert next(u for u in units if u["id"] == cands[0]["id"])["status"] == "AVAILABLE"
    # citizen sees the unit history on the tracker
    t = client.get(f"/api/v1/incidents/{d['incident_id']}/track", headers={"X-Tracking-Token": d["tracking_token"]}).json()
    assert t["dispatches"][0]["unit_type"] in ("FIRE_TENDER", "RESCUE_TENDER")


def test_crew_link_status_and_gps(client, auth, report):
    lat, lng = chennai()
    d = report("Man collapsed and is not breathing", lat, lng)
    cands = client.get(f"/api/v1/control-room/incidents/{d['incident_id']}/units", headers=auth["HOSPITAL"]).json()
    v = view(client, auth, "HOSPITAL", d["incident_id"])
    if not any(x["department"] == "HOSPITAL" for x in v["dispatches"]):
        client.post(f"/api/v1/control-room/incidents/{d['incident_id']}/dispatch", json={"unit_id": cands[0]["id"]}, headers=auth["HOSPITAL"])
        v = view(client, auth, "HOSPITAL", d["incident_id"])
    amb = next(x for x in v["dispatches"] if x["department"] == "HOSPITAL")
    uid = amb["unit"]["id"]
    assert client.post(f"/api/v1/control-room/units/{uid}/crew-link", headers=auth["POLICE"]).status_code == 404
    path = client.post(f"/api/v1/control-room/units/{uid}/crew-link", headers=auth["HOSPITAL"]).json()["path"]
    tok = path.split("t=")[1]
    assert client.get(f"/api/v1/crew/{uid}", headers={"X-Crew-Token": "wrong"}).status_code == 401
    job = client.get(f"/api/v1/crew/{uid}", headers={"X-Crew-Token": tok}).json()["job"]
    assert job["incident"]["id"] == v["incident_id"] and job["destination"]["name"]
    assert client.post(f"/api/v1/crew/{uid}/location", headers={"X-Crew-Token": tok},
                       json={"latitude": lat + 0.01, "longitude": lng}).status_code == 200
    for s in ("EN_ROUTE", "ON_SCENE", "TRANSPORTING", "AT_HOSPITAL", "COMPLETED"):
        if s == "EN_ROUTE" and client.get(f"/api/v1/crew/{uid}", headers={"X-Crew-Token": tok}).json()["job"]["dispatch"]["status"] != "ASSIGNED":
            continue
        assert client.post(f"/api/v1/crew/{uid}/status", headers={"X-Crew-Token": tok}, json={"status": s}).status_code == 200
    assert client.get(f"/api/v1/crew/{uid}", headers={"X-Crew-Token": tok}).json()["job"] is None
    finish(client, auth, view(client, auth, "ADMIN", d["incident_id"]))


@pytest.fixture
def fake_translation(monkeypatch):
    from app.services import translation_service

    def fake(text, src, tgt):
        if tgt == "en":
            return "A car hit a bike near the signal. Two people are injured.", "MyMemory machine translation"
        return f"[{tgt}] {text}", "MyMemory machine translation"
    monkeypatch.setattr(translation_service, "translate", fake)


def test_telugu_report_is_translated_for_control_rooms(client, auth, report, fake_translation):
    lat, lng = 12.62 + random.random() * 0.05, 77.10 + random.random() * 0.05
    d = report("సిగ్నల్ దగ్గర కారు బైక్‌ను ఢీకొంది. ఇద్దరు గాయపడ్డారు.", lat, lng, preferred_language="te")
    v = view(client, auth, "POLICE", d["incident_id"])
    assert v["english_summary"].startswith("A car hit a bike") and v["translation"]["from_language"] == "te"
    assert v["reports"][0]["english_kind"] == "machine_translation" and "original_text" not in v["reports"][0]
    assert "original_text" not in v                                    # originals stay admin-only
    assert view(client, auth, "ADMIN", d["incident_id"])["original_text"].startswith("సిగ్నల్")
    assert v["injuries"] == 2                                          # facts also read from the translation
    # responder note is translated back for the citizen
    client.post(f"/api/v1/control-room/incidents/{d['incident_id']}/status",
                json={"status": "RESPONDING", "note": "Ambulance is coming", "public": True}, headers=auth["POLICE"])
    t = client.get(f"/api/v1/incidents/{d['incident_id']}/track", headers={"X-Tracking-Token": d["tracking_token"]}).json()
    u = next(x for x in t["updates"] if x.get("note_original") == "Ambulance is coming")
    assert u["note_translated"] is True and u["note"].startswith("[te]")


def test_person_collapse_is_medical_not_structural():
    from app.services.ai_service import AIService
    assert AIService._rule_based("Old man collapsed at the bus stop", "en").category == "medical"
    assert AIService._rule_based("The building collapsed, people trapped", "en").category == "structural_collapse"


def test_not_routed_message_is_clear(client, auth, report, unique_point):
    lat, lng = unique_point()
    d = report("Kitchen fire, smoke everywhere, nobody inside", lat, lng)
    r = client.get(f"/api/v1/control-room/incidents/{d['incident_id']}", headers=auth["DISASTER"])
    assert r.status_code == 404 and "not in your service's queue" in r.json()["detail"]["message"]


def test_osm_import_parser_keeps_named_real_facilities_only():
    from app.db.import_osm_facilities import parse
    rows = parse({"elements": [
        {"type": "way", "id": 1, "center": {"lat": 13.08, "lon": 80.27}, "tags": {"amenity": "hospital", "name": "A Hospital", "emergency": "yes"}},
        {"type": "node", "id": 2, "lat": 12.92, "lon": 80.10, "tags": {"amenity": "fire_station", "name": "B Fire Station"}},
        {"type": "node", "id": 3, "lat": 12.95, "lon": 80.14, "tags": {"amenity": "police"}},                      # unnamed
        {"type": "node", "id": 4, "lat": 12.97, "lon": 80.22, "tags": {"amenity": "hospital", "healthcare": "clinic", "name": "C"}},
        {"type": "node", "id": 5, "lat": 12.90, "lon": 80.09, "tags": {"emergency": "ambulance_station", "name": "D Ambulance"}},
    ]})
    assert [(r["id"], r["type"]) for r in rows] == [("OSM-W1", "HOSPITAL"), ("OSM-N2", "FIRE"), ("OSM-N5", "AMBULANCE")]
    assert "Emergency department (per OSM)" in rows[0]["caps"]
