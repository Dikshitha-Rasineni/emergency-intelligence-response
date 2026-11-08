"""IoT ingestion: false-alarm prevention, idempotency, device auth, location, convergence."""
H = {"Authorization": "Bearer test-device-token"}


def post(client, body, headers=H):
    return client.post("/api/v1/iot/events", json=body, headers=headers)


def test_device_token_required(client):
    assert post(client, {"device_id": "DEV-X", "event_type": "TELEMETRY"}, headers={}).status_code == 401


def test_routine_telemetry_never_creates_incident(client):                             # 38
    r = post(client, {"device_id": "RESQ-ESP32-001", "event_id": "t:1", "event_type": "TELEMETRY",
                      "temperature": 31.0, "mq2_filtered_adc": 600}).json()
    assert r["status"] == "STORED" and r["incident_id"] is None


def test_unqualified_accident_type_does_not_create_incident(client):                  # audit bug #1
    r = post(client, {"device_id": "RESQ-ESP32-001", "event_id": "t:2", "event_type": "ACCIDENT", "alert_qualified": False}).json()
    assert r["status"] == "STORED" and r["incident_id"] is None


def test_simulated_alert_never_creates_incident(client):
    r = post(client, {"device_id": "RESQ-ESP32-001", "event_id": "t:3", "event_type": "FIRE",
                      "alert_qualified": True, "simulated": True}).json()
    assert r["incident_id"] is None


def test_duplicate_event_is_idempotent(client):                                        # 39, 47
    body = {"device_id": "DEV-DUP", "event_id": "DEV-DUP:1:9", "event_type": "FIRE", "alert_qualified": True,
            "latitude": 12.99, "longitude": 77.51, "reason": "mq2_analog_threshold"}
    a = post(client, body)
    b = post(client, body)
    assert a.status_code == 201 and b.status_code == 200
    assert a.json()["incident_id"] == b.json()["incident_id"] and b.json()["status"] == "DUPLICATE"


def test_qualified_fire_creates_incident_routed_to_fire(client, auth):                 # 7
    r = post(client, {"device_id": "DEV-FIRE", "event_id": "DEV-FIRE:1:1", "event_type": "FIRE", "alert_qualified": True,
                      "latitude": 12.881, "longitude": 77.455, "source_sensor": "mq2_analog", "observed_value": 900,
                      "threshold_value": 800, "measurement_unit": "adc_delta", "reason": "mq2_analog_threshold"}).json()
    assert r["status"] == "INCIDENT_CREATED"
    v = client.get(f"/api/v1/control-room/incidents/{r['incident_id']}", headers=auth["FIRE"]).json()
    assert v["source"] == "IOT" and v["sensor_evidence"][0]["observed_value"] == 900
    assert "not confirmed by a person" in " ".join(v["uncertainties"]).lower()


def test_qualified_flood_routes_to_disaster(client, auth):                             # 8
    r = post(client, {"device_id": "DEV-FLOOD", "event_id": "DEV-FLOOD:1:1", "event_type": "FLOOD",
                      "alert_qualified": True, "latitude": 12.70, "longitude": 77.70, "reason": "water_level_threshold"}).json()
    assert client.get(f"/api/v1/control-room/incidents/{r['incident_id']}", headers=auth["DISASTER"]).status_code == 200


def test_registered_location_used_and_missing_location_rejected(client):              # 43
    assert post(client, {"device_id": "RESQ-ESP32-001", "event_id": "loc:1", "event_type": "ACCIDENT",
                         "alert_qualified": True, "reason": "qualified_abnormal_motion"}).json()["incident_id"]
    r = post(client, {"device_id": "DEV-NOLOC", "event_id": "loc:2", "event_type": "ACCIDENT", "alert_qualified": True}).json()
    assert r["status"] == "REJECTED_NO_LOCATION" and r["incident_id"] is None


def test_invalid_coordinates_rejected(client):
    assert post(client, {"device_id": "DEV-BAD", "event_type": "TELEMETRY", "latitude": 123, "longitude": 77}).status_code == 422


def test_sensor_and_citizen_converge_into_one_incident(client, report, auth):          # 6 + convergence
    a = post(client, {"device_id": "DEV-ROAD", "event_id": "DEV-ROAD:1:1", "event_type": "ACCIDENT", "alert_qualified": True,
                      "latitude": 12.7801, "longitude": 77.3301, "reason": "qualified_abnormal_motion"}).json()
    d = report("Two bikes collided here, one rider injured", 12.7803, 77.3302)
    assert d["merged_into"] == a["incident_id"]
    v = client.get(f"/api/v1/control-room/incidents/{a['incident_id']}", headers=auth["POLICE"]).json()
    assert set(v["evidence_sources"]) == {"user_report", "iot_sensor"}
    assert v["linked_report_count"] == 1 and v["injuries"] == 1
    codes = [e["code"] for e in v["priority_evidence"]["evidence"]]
    assert codes.count("sensor_corroboration") == 1  # correlated evidence counted once, capped


def _depts(client, auth, iid):
    v = client.get(f"/api/v1/control-room/incidents/{iid}", headers=auth["ADMIN"]).json()
    return {d["department"]: d["role"] for d in v["routing"] if d["included"]}


def test_crash_sensor_alone_dispatches_hospital_and_police(client, auth):              # headline flow
    r = post(client, {"device_id": "DEV-CRASH", "event_id": "DEV-CRASH:1:1", "event_type": "ACCIDENT", "alert_qualified": True,
                      "latitude": 12.6101, "longitude": 77.2101, "acceleration_magnitude_g": 3.8,
                      "reason": "qualified_abnormal_motion"}).json()
    assert r["status"] == "INCIDENT_CREATED"
    d = _depts(client, auth, r["incident_id"])
    assert d["HOSPITAL"] == "PRIMARY" and d["POLICE"] == "PRIMARY" and "FIRE" not in d
    h = client.get(f"/api/v1/control-room/incidents/{r['incident_id']}", headers=auth["HOSPITAL"]).json()
    assert h["sensor_evidence"] and h["source"] == "IOT"


def test_severe_crash_sensor_also_alerts_fire_and_raises_priority(client, auth):
    r = post(client, {"device_id": "DEV-CRASH2", "event_id": "DEV-CRASH2:1:1", "event_type": "ACCIDENT", "alert_qualified": True,
                      "latitude": 12.6301, "longitude": 77.2301, "acceleration_magnitude_g": 6.4,
                      "hazard_severity": "CRITICAL", "reason": "severe_impact"}).json()
    d = _depts(client, auth, r["incident_id"])
    assert set(d) == {"HOSPITAL", "POLICE", "FIRE"} and d["FIRE"] == "SUPPORTING"
    v = client.get(f"/api/v1/control-room/incidents/{r['incident_id']}", headers=auth["ADMIN"]).json()
    assert "sensor_severe" in [e["code"] for e in v["priority_evidence"]["evidence"]]


def test_fire_sensor_alerts_fire_hospital_police(client, auth):
    r = post(client, {"device_id": "DEV-FIRE2", "event_id": "DEV-FIRE2:1:1", "event_type": "FIRE", "alert_qualified": True,
                      "latitude": 12.6501, "longitude": 77.2501, "reason": "smoke_and_heat"}).json()
    d = _depts(client, auth, r["incident_id"])
    assert d == {"FIRE": "PRIMARY", "HOSPITAL": "SUPPORTING", "POLICE": "SUPPORTING"}


def test_sensor_merging_into_report_updates_routing(client, report, auth):
    rep = report("Two cars collided, one driver injured", 12.6701, 77.2701)
    r = post(client, {"device_id": "DEV-CRASH3", "event_id": "DEV-CRASH3:1:1", "event_type": "ACCIDENT", "alert_qualified": True,
                      "latitude": 12.6702, "longitude": 77.2702, "acceleration_magnitude_g": 7.0,
                      "hazard_severity": "CRITICAL", "reason": "severe_impact"}).json()
    assert r["status"] == "MERGED_INTO_INCIDENT" and r["incident_id"] == rep["incident_id"]
    assert "FIRE" in _depts(client, auth, rep["incident_id"])


def test_admin_demo_trigger_uses_real_pipeline(client, auth):
    assert client.post("/api/v1/iot/devices/RESQ-ESP32-002/demo-alert", json={"event_type": "FIRE"},
                       headers=auth["FIRE"]).status_code == 403
    r = client.post("/api/v1/iot/devices/RESQ-ESP32-002/demo-alert", json={"event_type": "FIRE"}, headers=auth["ADMIN"])
    assert r.status_code == 200 and r.json()["incident_id"]
    devs = client.get("/api/v1/iot/devices", headers=auth["POLICE"]).json()
    assert any(x["device_id"] == "RESQ-ESP32-002" and x["alerts_total"] >= 1 for x in devs)
