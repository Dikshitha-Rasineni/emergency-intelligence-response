import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.incident import EmergencyReport

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_create_canonical_incident():
    payload = {
        "description": "Major accident near highway. Three people are injured and one person is unconscious.",
        "latitude": 12.9352,
        "longitude": 77.6944,
        "location": "Outer Ring Road, KM 14.2 Southbound, Bengaluru",
        "affected_people": 3,
        "injuries": 3,
    }
    response = client.post("/api/v1/incidents", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["incident_id"].startswith("INC-")
    assert "accident" in data["emergency_type"].lower()
    assert data["injuries"] == 3
    assert data["priority_score"] >= 75
    assert data["severity"] == "CRITICAL"
    assert any("unconscious" in ind.lower() for ind in data["critical_indicators"])

    # Verify real DB persistence
    db = SessionLocal()
    try:
        report = db.query(EmergencyReport).filter(EmergencyReport.id == data["incident_id"]).first()
        assert report is not None
        assert report.description == payload["description"]
        assert len(report.ai_extractions) > 0
        assert len(report.severity_assessments) > 0
    finally:
        db.close()


def test_list_and_get_incidents():
    list_res = client.get("/api/v1/incidents")
    assert list_res.status_code == 200
    incidents = list_res.json()
    assert len(incidents) > 0

    first_id = incidents[0]["incident_id"]
    get_res = client.get(f"/api/v1/incidents/{first_id}")
    assert get_res.status_code == 200
    assert get_res.json()["incident_id"] == first_id


def test_nearby_resources():
    params = {
        "latitude": 12.9352,
        "longitude": 77.6944,
        "radius": 15.0,
    }
    response = client.get("/api/v1/resources/nearby", params=params)
    assert response.status_code == 200
    resources = response.json()
    assert len(resources) > 0

    # Ensure real distance and ETA are calculated
    first = resources[0]
    assert first["distance_km"] > 0
    assert first["eta_min"] > 0
    assert "availability" in first


def test_resource_ranking():
    payload = {
        "latitude": 12.9352,
        "longitude": 77.6944,
        "emergency_type": "Major Road Accident",
        "injuries": 3,
        "affected_people": 3,
        "max_radius_km": 20.0,
    }
    response = client.post("/api/v1/resources/rank", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] > 0
    # Top resource should have ranking 1 and high suitability
    top = data["resources"][0]
    assert top["ranking"] == 1
    assert top["suitability_score"] > 50.0


def test_route_calculation():
    params = {
        "origin_lat": 12.9550,
        "origin_lng": 77.6500,
        "destination_lat": 12.9352,
        "destination_lng": 77.6944,
        "origin_name": "City Care Hospital",
        "destination_name": "Accident Site",
    }
    response = client.get("/api/v1/routes", params=params)
    assert response.status_code == 200
    route = response.json()
    assert route["distance_km"] > 0
    assert route["eta_min"] > 0
    assert len(route["coordinates"]) > 2
    assert len(route["steps"]) >= 4


def test_ai_precautions():
    payload = {
        "emergency_type": "Commercial Building Fire",
        "description": "Dense smoke billowing from kitchen",
        "priority_score": 80,
    }
    response = client.post("/api/ai/precautions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["precautions"]) >= 3
    assert any("smoke" in p.lower() or "elevator" in p.lower() for p in data["precautions"])


def test_role_intelligence():
    payload = {
        "role": "HOSPITAL",
        "emergency_type": "Major Road Accident",
        "description": "High-impact collision with 3 casualties",
        "affected_people": 3,
        "injuries": 3,
        "critical_indicators": ["Unconscious casualty"],
        "priority_score": 85,
    }
    response = client.post("/api/v1/ai/response", json=payload)
    assert response.status_code == 200
    intel = response.json()
    assert intel["role"] == "HOSPITAL"
    assert len(intel["operational_checklist"]) > 0
    assert len(intel["required_services"]) > 0


def test_iot_event_ingestion():
    payload = {
        "device_id": "ESP32_CRASH_NODE_01",
        "event_type": "ACCIDENT",
        "temperature": 32.5,
        "smoke_level": 400.0,
        "impact": 8.7,  # > 5.0 G trigger threshold
        "latitude": 12.9352,
        "longitude": 77.6944,
    }
    response = client.post("/api/v1/iot/events", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PROCESSED"
    assert data["incident_id"] is not None
    assert data["severity"] in ["CRITICAL", "HIGH"]
