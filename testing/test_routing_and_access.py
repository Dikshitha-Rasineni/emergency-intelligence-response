"""Department routing policy, field-level filtering, authorization, notifications, operations."""
from datetime import datetime, timedelta, timezone

from app.services import department_routing_service as policy


def included(decisions):
    return {d["department"]: d["role"] for d in decisions if d["included"]}


def test_fire_routes_to_fire_and_hospital_when_people_present():                      # 30
    r = included(policy.decide({"category": "fire", "affected_people": 3, "hazards": ["smoke"]}))
    assert r["FIRE"] == "PRIMARY" and r["HOSPITAL"] == "SUPPORTING" and "DISASTER" not in r


def test_road_accident_hospital_and_police_not_fire():                                 # 31, 32
    d = policy.decide({"category": "road_accident", "injuries": 2, "hazards": ["traffic"], "needs": ["medical"]})
    r = included(d)
    assert r == {"HOSPITAL": "PRIMARY", "POLICE": "PRIMARY"}
    fire = next(x for x in d if x["department"] == "FIRE")
    assert "no fire" in fire["reasons"][0].lower()


def test_entrapment_activates_rescue():                                                # 33
    assert included(policy.decide({"category": "road_accident", "trapped": True}))["FIRE"] == "PRIMARY"


def test_mixed_accident_fire_activates_all_three():                                    # 34 / 9
    r = included(policy.decide({"category": "road_accident", "injuries": 1, "hazards": ["fire", "traffic"], "trapped": True}))
    assert {"HOSPITAL", "POLICE", "FIRE"} <= set(r)


def test_ambiguous_incident_escalates_safely():                                        # 35
    assert included(policy.decide({"category": "other"})) == {"POLICE": "ESCALATION"}
    assert included(policy.decide({"category": "sos", "severity": "HIGH"})) == {"POLICE": "ESCALATION", "HOSPITAL": "ESCALATION"}


def test_flood_routes_disaster_and_rescue():
    r = included(policy.decide({"category": "flood", "needs": ["rescue"], "affected_people": 2}))
    assert r["DISASTER"] == "PRIMARY" and r["FIRE"] == "PRIMARY"


def test_unrouted_department_cannot_see_incident(client, report, auth, unique_point):   # 36
    lat, lng = unique_point()
    d = report("Small fire in a dustbin outside the shop, no one hurt", lat, lng)
    iid = d["incident_id"]
    assert client.get(f"/api/v1/control-room/incidents/{iid}", headers=auth["FIRE"]).status_code == 200
    assert client.get(f"/api/v1/control-room/incidents/{iid}", headers=auth["DISASTER"]).status_code == 404
    listing = client.get("/api/v1/control-room/incidents", headers=auth["DISASTER"]).json()
    assert iid not in [i["incident_id"] for i in listing["items"]]
    assert client.get(f"/api/v1/control-room/incidents/{iid}").status_code == 401
    assert client.get("/api/v1/admin/users", headers=auth["FIRE"]).status_code == 403


def test_field_level_filtering(client, report, auth, unique_point):                    # 37
    lat, lng = unique_point()
    d = report("Car crash, driver unconscious and trapped, petrol leaking", lat, lng)
    iid = d["incident_id"]
    police = client.get(f"/api/v1/control-room/incidents/{iid}", headers=auth["POLICE"]).json()
    hospital = client.get(f"/api/v1/control-room/incidents/{iid}", headers=auth["HOSPITAL"]).json()
    fire = client.get(f"/api/v1/control-room/incidents/{iid}", headers=auth["FIRE"]).json()
    assert "unconscious" not in police and "medical_needs" not in police and "original_text" not in police
    assert hospital["unconscious"] is True and "hazards" not in hospital and "sensor_evidence" in hospital
    assert "hazards" in fire and "unconscious" not in fire
    for v in (police, hospital, fire):
        assert all(r["type"] in {"POLICE": {"POLICE"}, "HOSPITAL": {"HOSPITAL", "AMBULANCE"}, "FIRE": {"FIRE"}}[v["department_view"]]
                   for r in v["resources"])
        assert v["brief"]["facts"] and "not dispatch orders" in v["brief"]["notice"]


def test_route_unavailable_is_not_fabricated(client, report, auth):
    d = report("Fire near the demo Egmore fire station", 13.0736, 80.2614)
    v = client.get(f"/api/v1/control-room/incidents/{d['incident_id']}", headers=auth["FIRE"]).json()
    assert v["route"]["available"] is False
    assert v["route"]["coordinates"] == [] and v["route"]["eta_min"] is None
    assert v["route"]["straight_line_km"] >= 0


def test_acknowledge_status_and_citizen_updates(client, report, auth, unique_point):
    lat, lng = unique_point()
    d = report("Fire in a parked scooter", lat, lng)
    iid, tok = d["incident_id"], d["tracking_token"]
    n = client.post(f"/api/v1/control-room/incidents/{iid}/acknowledge", headers=auth["FIRE"]).json()
    assert n["status"] == "ACKNOWLEDGED"
    assert [h["status"] for h in n["history"]][:2] == ["CREATED", "PENDING"]   # never claimed DELIVERED
    r = client.post(f"/api/v1/control-room/incidents/{iid}/status", headers=auth["FIRE"],
                    json={"status": "RESPONDING", "note": "Fire tender on the way", "public": True})
    assert r.status_code == 200
    track = client.get(f"/api/v1/incidents/{iid}/track", headers={"X-Tracking-Token": tok}).json()
    assert track["status"] == "RESPONDING"
    assert any(u["note"] == "Fire tender on the way" for u in track["updates"])
    assert client.post(f"/api/v1/control-room/incidents/{iid}/acknowledge", headers=auth["POLICE"]).status_code == 404


def test_priority_override_is_audited(client, report, auth, unique_point):
    lat, lng = unique_point()
    iid = report("Gas smell in the basement", lat, lng)["incident_id"]
    r = client.post(f"/api/v1/control-room/incidents/{iid}/priority-override", headers=auth["FIRE"],
                    json={"score": 90, "reason": "Large LPG store confirmed by caller"})
    assert r.json()["priority_score"] == 90 and r.json()["severity"] == "CRITICAL"
    v = client.get(f"/api/v1/control-room/incidents/{iid}", headers=auth["ADMIN"]).json()
    assert v["priority_evidence"]["override_reason"] == "Large LPG store confirmed by caller"
    audit = client.get("/api/v1/admin/audit?action=incident.priority_override", headers=auth["ADMIN"]).json()
    assert any(a["target_id"] == iid for a in audit["items"])


def test_notification_escalates_after_deadline(client, report, auth, unique_point):
    from app.db.session import SessionLocal
    from app.models.operations import Notification
    lat, lng = unique_point()
    iid = report("Flood water rising in the colony, 30 houses affected", lat, lng)["incident_id"]
    db = SessionLocal()
    for n in db.query(Notification).filter_by(incident_id=iid).all():
        n.ack_deadline = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit(); db.close()
    client.get("/api/v1/control-room/incidents", headers=auth["DISASTER"])  # triggers escalation sweep
    v = client.get(f"/api/v1/control-room/incidents/{iid}", headers=auth["DISASTER"]).json()
    assert v["notification"]["status"] == "ESCALATED"


def test_resolve_cancels_open_notifications(client, report, auth, unique_point):
    lat, lng = unique_point()
    iid = report("Bike accident, rider injured", lat, lng)["incident_id"]
    client.post(f"/api/v1/control-room/incidents/{iid}/status", headers=auth["POLICE"], json={"status": "RESOLVED"})
    v = client.get(f"/api/v1/control-room/incidents/{iid}", headers=auth["ADMIN"]).json()
    assert {n["department"]: n["status"] for n in v["notifications"]}["HOSPITAL"] == "CANCELLED"


def test_websocket_pushes_to_routed_department_only(client, auth, report, unique_point):
    fire_tok = auth["FIRE"]["Authorization"].split()[1]
    lat, lng = unique_point()
    with client.websocket_connect(f"/api/v1/ws/control-room?token={fire_tok}") as ws:
        assert ws.receive_json()["type"] == "hello"
        iid = report("Fire in the electrical panel room", lat, lng)["incident_id"]
        msgs = [ws.receive_json() for _ in range(2)]
        assert any(m.get("type") == "incident.notification" for m in msgs)
        note = next(m for m in msgs if m.get("type") == "incident.notification")
        ws.send_json({"type": "delivered", "notification_id": note["notification_id"]})
    import time; time.sleep(0.3)
    v = client.get(f"/api/v1/control-room/incidents/{iid}", headers=auth["FIRE"]).json()
    assert v["notification"]["status"] == "DELIVERED"


def test_nearby_resources_postgis_and_unknown_availability(client):
    rs = client.get("/api/v1/resources/nearby?latitude=13.0418&longitude=80.2341&radius=5").json()
    assert rs and rs == sorted(rs, key=lambda r: r["distance_km"])
    assert all(r["availability_status"] == "UNKNOWN" and r["data_source"] == "DEMO_SEED" and r["phone"] is None for r in rs)


def test_availability_only_by_operating_org(client, auth):
    body = {"status": "AVAILABLE", "available_units": 2}
    assert client.post("/api/v1/admin/resources/DEMO-F1/availability", json=body, headers=auth["POLICE"]).status_code == 403
    assert client.post("/api/v1/admin/resources/DEMO-F1/availability", json=body, headers=auth["FIRE"]).status_code == 200
    r = next(x for x in client.get("/api/v1/resources/nearby?latitude=13.0732&longitude=80.2609&radius=1").json() if x["id"] == "DEMO-F1")
    assert r["availability_status"] == "AVAILABLE" and r["availability_verified"] is True


def test_knowledge_only_approved_documents_are_retrieved(client, auth):
    body = ("Flood safety. Do not walk through moving water. Six inches of moving water can knock you down. "
            "Move to higher ground and avoid electrical equipment if you are wet.")
    doc = client.post("/api/v1/admin/knowledge", headers=auth["ADMIN"], data={
        "title": "Test flood leaflet", "publisher": "Test Authority", "categories": "flood", "body": body}).json()
    before = client.get("/api/v1/admin/knowledge/search?q=moving water&category=flood", headers=auth["FIRE"]).json()
    assert all(h["publisher"] != "Test Authority" for h in before)  # unapproved: never retrieved
    client.post(f"/api/v1/admin/knowledge/{doc['id']}/approve", headers=auth["ADMIN"])
    hits = client.get("/api/v1/admin/knowledge/search?q=moving water&category=flood", headers=auth["FIRE"]).json()
    mine = [h for h in hits if h["publisher"] == "Test Authority"]
    assert mine and "moving water" in mine[0]["excerpt"]
