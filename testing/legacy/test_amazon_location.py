"""
Amazon Location Service integration tests for RESQ.AI.

Tests:
  1.  AWS configuration present in settings
  2.  LocationService.calculate_route returns valid structure or None (graceful)
  3.  LocationService.calculate_route invalid coordinates handled
  4.  RoutingService.calculate_route returns RouteResponse with Amazon Location or fallback
  5.  Route distance > 0 and ETA > 0
  6.  Route geometry has at least 2 coordinate points
  7.  routing_status field is set and non-empty
  8.  Map style proxy endpoint responds (200 or 503 — never 500)
  9.  Map tile proxy endpoint responds (200 or 503 — never 500)
  10. End-to-end: incident → nearby resources → route calculation
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.location_service import LocationService
from app.services.routing_service import RoutingService

client = TestClient(app)

# Known Bengaluru test coordinates
HOSPITAL_LAT, HOSPITAL_LNG = 12.9550, 77.6500   # City Care Hospital
INCIDENT_LAT, INCIDENT_LNG = 12.9352, 77.6944   # Outer Ring Road accident site


# ---------------------------------------------------------------------------
# 1. AWS configuration
# ---------------------------------------------------------------------------

def test_aws_region_configured():
    assert settings.AWS_REGION, "AWS_REGION must be set"
    assert settings.AWS_REGION == "us-east-1"


def test_aws_location_map_configured():
    assert settings.AWS_LOCATION_MAP_NAME == "resq-ai-maps"


def test_aws_location_route_calculator_configured():
    assert settings.AWS_LOCATION_ROUTE_CALCULATOR == "resq-ai-routing"


# ---------------------------------------------------------------------------
# 2-3. LocationService unit tests
# ---------------------------------------------------------------------------

def test_location_service_calculate_route_returns_dict_or_none():
    """Amazon Location route returns a valid dict or None — never raises."""
    result = LocationService.calculate_route(
        HOSPITAL_LAT, HOSPITAL_LNG, INCIDENT_LAT, INCIDENT_LNG
    )
    if result is not None:
        assert "distance_meters" in result
        assert "duration_seconds" in result
        assert "geometry" in result
        assert isinstance(result["geometry"], list)
        assert result["distance_meters"] > 0
        assert result["duration_seconds"] > 0
        assert result["source"] == "AMAZON_LOCATION"


def test_location_service_invalid_coordinates_handled():
    """Out-of-range coordinates must not raise — return None gracefully."""
    result = LocationService.calculate_route(999.0, 999.0, 999.0, 999.0)
    assert result is None


# ---------------------------------------------------------------------------
# 4-7. RoutingService (Amazon Location → OSRM → fallback chain)
# ---------------------------------------------------------------------------

def test_routing_service_returns_route_response():
    route = RoutingService.calculate_route(
        origin_lat=HOSPITAL_LAT,
        origin_lng=HOSPITAL_LNG,
        destination_lat=INCIDENT_LAT,
        destination_lng=INCIDENT_LNG,
        origin_name="City Care Hospital",
        destination_name="Accident Site",
    )
    assert route is not None
    assert route.distance_km > 0
    assert route.eta_min > 0


def test_route_geometry_has_points():
    route = RoutingService.calculate_route(
        HOSPITAL_LAT, HOSPITAL_LNG, INCIDENT_LAT, INCIDENT_LNG
    )
    assert len(route.coordinates) >= 2
    # Each coordinate must be [lat, lng]
    for coord in route.coordinates:
        assert len(coord) == 2
        lat, lng = coord
        assert -90 <= lat <= 90
        assert -180 <= lng <= 180


def test_route_has_routing_status():
    route = RoutingService.calculate_route(
        HOSPITAL_LAT, HOSPITAL_LNG, INCIDENT_LAT, INCIDENT_LNG
    )
    assert route.routing_status
    assert route.routing_status in {
        "AMAZON_LOCATION_ROUTES",
        "OSRM_ROAD_NETWORK",
        "ACCURATE_OSRM_ROAD_NETWORK",
        "GIS_FALLBACK_MATRIX",
    }


def test_route_api_endpoint():
    """GET /api/v1/routes returns valid route data."""
    params = {
        "origin_lat": HOSPITAL_LAT,
        "origin_lng": HOSPITAL_LNG,
        "destination_lat": INCIDENT_LAT,
        "destination_lng": INCIDENT_LNG,
        "origin_name": "City Care Hospital",
        "destination_name": "Accident Site",
    }
    response = client.get("/api/v1/routes", params=params)
    assert response.status_code == 200
    data = response.json()
    assert data["distance_km"] > 0
    assert data["eta_min"] > 0
    assert len(data["coordinates"]) >= 2
    assert data["routing_status"] in {
        "AMAZON_LOCATION_ROUTES",
        "OSRM_ROAD_NETWORK",
        "ACCURATE_OSRM_ROAD_NETWORK",
        "GIS_FALLBACK_MATRIX",
    }


# ---------------------------------------------------------------------------
# 8-9. Map proxy endpoints
# ---------------------------------------------------------------------------

def test_map_style_endpoint_never_500():
    """Map style proxy must return 200 or 503 — never an unhandled 500."""
    response = client.get("/api/v1/maps/style.json")
    assert response.status_code in (200, 503)


def test_map_tile_endpoint_never_500():
    """Map tile proxy must return 200 or 503 — never an unhandled 500."""
    response = client.get("/api/v1/maps/tiles/13/6584/3180")
    assert response.status_code in (200, 503)


def test_map_glyphs_endpoint_never_500():
    response = client.get("/api/v1/maps/glyphs/Arial Unicode MS Regular/0-255.pbf")
    assert response.status_code in (200, 503)


def test_map_sprites_endpoint_never_500():
    response = client.get("/api/v1/maps/sprites/sprites.json")
    assert response.status_code in (200, 503)


# ---------------------------------------------------------------------------
# 10. End-to-end: ACCIDENT → resources → Amazon Location route
# ---------------------------------------------------------------------------

def test_end_to_end_accident_route():
    """
    Full pipeline:
      POST /incidents  →  GET /resources/nearby  →  GET /routes
    Verifies that a real incident flows through to a verified route.
    """
    # Step 1: Create incident
    incident_payload = {
        "description": "Major accident near highway. Three people injured, one unconscious.",
        "latitude": INCIDENT_LAT,
        "longitude": INCIDENT_LNG,
        "location": "Outer Ring Road, Bengaluru",
        "affected_people": 3,
        "injuries": 3,
        "source": "USER",
    }
    inc_resp = client.post("/api/v1/incidents", json=incident_payload)
    assert inc_resp.status_code == 201
    incident = inc_resp.json()
    assert incident["priority_score"] >= 50

    # Step 2: Find nearby resources
    res_resp = client.get("/api/v1/resources/nearby", params={
        "latitude": INCIDENT_LAT,
        "longitude": INCIDENT_LNG,
        "radius": 20.0,
    })
    assert res_resp.status_code == 200
    resources = res_resp.json()
    assert len(resources) > 0

    # Pick the nearest hospital
    hospitals = [r for r in resources if r.get("resource_type") == "HOSPITAL" or r.get("type") == "HOSPITAL"]
    top_resource = hospitals[0] if hospitals else resources[0]

    res_lat = top_resource.get("latitude") or top_resource.get("lat")
    res_lng = top_resource.get("longitude") or top_resource.get("lng")
    assert res_lat and res_lng

    # Step 3: Calculate route from resource to incident
    route_resp = client.get("/api/v1/routes", params={
        "origin_lat": res_lat,
        "origin_lng": res_lng,
        "destination_lat": INCIDENT_LAT,
        "destination_lng": INCIDENT_LNG,
        "origin_name": top_resource["name"],
        "destination_name": "Accident Site",
    })
    assert route_resp.status_code == 200
    route = route_resp.json()

    # Verify actual values — not fabricated
    assert route["distance_km"] > 0, "Distance must be > 0"
    assert route["eta_min"] > 0, "ETA must be > 0"
    assert len(route["coordinates"]) >= 2, "Route must have geometry"
    assert route["routing_status"], "routing_status must be set"

    print(f"\n[E2E TEST RESULT]")
    print(f"  Incident:       {incident['incident_id']} | Priority: {incident['priority_score']}/100")
    print(f"  Resource:       {top_resource['name']} ({top_resource.get('resource_type') or top_resource.get('type')})")
    print(f"  Distance:       {route['distance_km']} km")
    print(f"  ETA:            {route['eta_min']} min")
    print(f"  Geometry pts:   {len(route['coordinates'])}")
    print(f"  Routing source: {route['routing_status']}")
