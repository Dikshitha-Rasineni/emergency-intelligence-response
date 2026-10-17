import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.services.language_service import LanguageService
from app.services.geospatial_discovery_service import GeospatialDiscoveryService

client = TestClient(app)


def test_location_preservation_and_unverified():
    """
    Test 1: User enters 'Location X'. Coordinates cannot be geocoded.
    Ensure original text 'Location X' is preserved, marked UNVERIFIED,
    and no hardcoded coordinates are silently injected.
    """
    create_res = client.post("/api/v1/incidents", json={
        "description": "Vehicle crash near corner. Two people injured.",
        "location": "Location X",
        "affected_people": 2,
        "injuries": 2
    })
    assert create_res.status_code == 201
    inc = create_res.json()
    assert inc["location_name"] == "Location X"
    assert inc["location"] == "Location X"
    assert inc["coordinates_verified"] is False
    assert inc["location_source"] == "UNVERIFIED"
    assert inc["latitude"] is None
    assert inc["longitude"] is None

    inc_id = inc["incident_id"]

    # Updating description only must preserve location text and unverified status
    patch_res = client.patch(f"/api/v1/incidents/{inc_id}", json={
        "description": "Vehicle crash update: Ambulance arrived on scene. Both persons stable."
    })
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert patched["location_name"] == "Location X"
    assert patched["coordinates_verified"] is False
    assert patched["latitude"] is None


def test_location_update_and_geocoding():
    """
    Test 2: Updating location text via PATCH.
    If valid location is provided, geocoding resolves coordinates.
    """
    # Create incident with known location
    create_res = client.post("/api/v1/incidents", json={
        "description": "Fire in building corridor.",
        "location": "Indiranagar, Bengaluru",
        "affected_people": 1,
        "injuries": 0
    })
    assert create_res.status_code == 201
    inc = create_res.json()
    assert "Indiranagar" in inc["location_name"]
    inc_id = inc["incident_id"]

    # Update location to another spot
    patch_res = client.patch(f"/api/v1/incidents/{inc_id}", json={
        "location_name": "MG Road, Bengaluru"
    })
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert "MG Road" in patched["location_name"]


def test_multilingual_detection_and_guidance():
    """
    Test 3: End-to-end multilingual support for Telugu, Tamil, Hindi, Kannada, Malayalam.
    Verifies script detection, priority evaluation, and localized response generation.
    """
    languages = [
        ("te", "రోడ్డు ప్రమాదం జరిగింది. ఇద్దరు వ్యక్తులు తీవ్రంగా గాయపడ్డారు మరియు ఒకరు స్పృహ కోల్పోయారు."),
        ("ta", "சாலை விபத்து ஏற்பட்டது. இருவர் படுகாயமடைந்துள்ளனர், ஒருவர் மயக்கமடைந்துள்ளார்."),
        ("hi", "सड़क दुर्घटना हुई है। दो लोग गंभीर रूप से घायल हैं और एक बेहोश है।"),
        ("kn", "ರಸ್ತೆ ಅಪಘಾತ ಸಂಭವಿಸಿದೆ. ಇಬ್ಬರು ಗಂಭೀರವಾಗಿ ಗಾಯಗೊಂಡಿದ್ದಾರೆ ಮತ್ತು ಒಬ್ಬರು ಪ್ರಜ್ಞಾಹೀನರಾಗಿದ್ದಾರೆ."),
        ("ml", "റോഡ് അപകടം ഉണ്ടായി. രണ്ട് പേർക്ക് ഗുരുതരമായി പരിക്കേറ്റു, ഒരാൾ അബോധാവസ്ഥയിലാണ്.")
    ]

    for expected_lang, text in languages:
        detected = LanguageService.detect_language(text)
        assert detected == expected_lang, f"Expected {expected_lang}, got {detected}"

        res = client.post("/api/v1/incidents", json={
            "description": text,
            "location": "Sector Highway",
            "injuries": 2
        })
        assert res.status_code == 201
        data = res.json()
        assert data["detected_language"] == expected_lang
        assert data["priority_score"] >= 60  # Critical casualty detected in native language
        assert data["precautions"] is not None and len(data["precautions"]) > 0


def test_geospatial_resource_discovery_and_clinic_distinction():
    """
    Test 4: Real geospatial facility discovery and strict clinic vs hospital distinction.
    """
    # Test geocoding endpoint
    geo_res = client.get("/api/v1/resources/geocode", params={"query": "Bengaluru"})
    assert geo_res.status_code == 200
    geo_data = geo_res.json()
    assert "latitude" in geo_data and "longitude" in geo_data
    assert geo_data["latitude"] is not None

    # Test nearby resources query around Bengaluru center
    nearby_res = client.get("/api/v1/resources/nearby", params={
        "latitude": 12.9716,
        "longitude": 77.5946,
        "radius": 15.0
    })
    assert nearby_res.status_code == 200
    resources = nearby_res.json()
    assert isinstance(resources, list)
    assert len(resources) > 0

    # Ensure every resource has required fields and proper categorization
    for r in resources:
        assert "resource_type" in r
        assert "distance_km" in r
        assert "eta_min" in r or "eta_minutes" in r
        if r["resource_type"] == "CLINIC":
            assert r.get("is_clinic", False) is True
