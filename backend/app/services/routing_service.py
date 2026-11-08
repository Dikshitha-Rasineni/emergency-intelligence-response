"""Road routing. Provider order: Amazon Location (if configured) -> OSRM.
If both fail the response says so: no invented polyline, no invented ETA."""
from __future__ import annotations

import math
from typing import Optional

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.schemas.routing import RouteResponse, RouteStep

ETA_NOTE = "Provider estimate for normal traffic; actual emergency response time may differ."


class RoutingService:
    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371.0
        dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @classmethod
    def _osrm(cls, o_lat, o_lng, d_lat, d_lng):
        url = (f"{settings.OSRM_BASE_URL.rstrip('/')}/route/v1/driving/{o_lng},{o_lat};{d_lng},{d_lat}"
               f"?overview=full&geometries=geojson&steps=true")
        with httpx.Client(timeout=6.0, headers={"User-Agent": "RESQ.AI/2.0"}) as c:
            resp = c.get(url)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "Ok" or not data.get("routes"):
            raise ValueError(f"OSRM: {data.get('code')}")
        route = data["routes"][0]
        coords = [[round(lat, 5), round(lng, 5)] for lng, lat in route["geometry"]["coordinates"]]
        steps, names = [], []
        for st in (route.get("legs") or [{}])[0].get("steps", []):
            name = st.get("name") or ""
            if name and name not in names and len(names) < 3:
                names.append(name)
            m = st.get("maneuver", {})
            instr = " ".join(filter(None, [m.get("type", "").replace("_", " ").capitalize(), m.get("modifier"),
                                           f"onto {name}" if name else ""]))
            if st.get("distance", 0) > 50:
                steps.append(RouteStep(instruction=instr or "Continue", distance_km=round(st["distance"] / 1000, 2),
                                       duration_min=round(st.get("duration", 0) / 60, 1)))
        return coords, route["distance"] / 1000.0, route["duration"] / 60.0, steps[:10], " via ".join(names) or None

    @classmethod
    def _amazon(cls, o_lat, o_lng, d_lat, d_lng):
        if not settings.AWS_LOCATION_ROUTE_CALCULATOR:
            return None
        from app.services.location_service import LocationService
        r = LocationService.calculate_route(o_lat, o_lng, d_lat, d_lng)
        if not r or not r.get("geometry"):
            return None
        return r["geometry"], r["distance_meters"] / 1000.0, r["duration_seconds"] / 60.0

    @classmethod
    def calculate_route(cls, origin_lat: float, origin_lng: float, destination_lat: float, destination_lng: float,
                        origin_name: str = "Station", destination_name: str = "Incident location",
                        responder_role: Optional[str] = None) -> RouteResponse:
        straight = round(cls.haversine_distance_km(origin_lat, origin_lng, destination_lat, destination_lng), 2)
        base = dict(origin_name=origin_name, destination_name=destination_name, origin_lat=origin_lat,
                    origin_lng=origin_lng, destination_lat=destination_lat, destination_lng=destination_lng,
                    straight_line_km=straight)
        try:
            am = cls._amazon(origin_lat, origin_lng, destination_lat, destination_lng)
            if am:
                coords, km, mins = am
                return RouteResponse(available=True, provider="AMAZON_LOCATION", routing_status="AMAZON_LOCATION_ROUTES",
                                     distance_km=round(km, 1), eta_min=max(1, round(mins)), eta_note=ETA_NOTE,
                                     coordinates=coords, **base)
        except Exception as e:
            logger.warning(f"Amazon Location routing failed: {e}")
        try:
            coords, km, mins, steps, corridor = cls._osrm(origin_lat, origin_lng, destination_lat, destination_lng)
            return RouteResponse(available=True, provider="OSRM", routing_status="OSRM_ROAD_NETWORK",
                                 distance_km=round(km, 1), eta_min=max(1, round(mins)), eta_note=ETA_NOTE,
                                 route_corridor=corridor, steps=steps, coordinates=coords, **base)
        except Exception as e:
            logger.warning(f"OSRM routing failed: {e}")
        return RouteResponse(available=False, provider="UNAVAILABLE", routing_status="UNAVAILABLE",
                             message="No routing provider responded. Straight-line distance shown for reference only.",
                             **base)
