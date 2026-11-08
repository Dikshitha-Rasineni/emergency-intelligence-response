"""Nearby emergency resources.

Spatial filtering uses PostGIS (ST_DWithin / ST_Distance on geography columns).
Distances here are straight-line; road distance/ETA only come from RoutingService.
Availability is shown as UNKNOWN unless an authorized organisation user reported it.
Optional live lookup from OpenStreetMap is labelled with its source.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.resource import EmergencyResource
from app.schemas.resource import ResourceResponse
from app.services.geospatial_discovery_service import GeospatialDiscoveryService
from app.services.taxonomy import normalize_category

TYPES_FOR_CATEGORY = {
    "road_accident": ("HOSPITAL", "AMBULANCE", "POLICE"),
    "fire": ("FIRE", "HOSPITAL", "AMBULANCE"),
    "gas_leak": ("FIRE", "HOSPITAL"),
    "flood": ("DISASTER", "FIRE", "SHELTER", "HOSPITAL"),
    "medical": ("HOSPITAL", "AMBULANCE"),
    "structural_collapse": ("FIRE", "DISASTER", "HOSPITAL"),
    "rescue": ("FIRE", "DISASTER"),
    "security": ("POLICE",),
}


def _fmt(res: EmergencyResource, distance_km: Optional[float]) -> ResourceResponse:
    av = res.availability
    verified_av = bool(av and av.verified)
    status = av.status if verified_av else "UNKNOWN"
    label = {"AVAILABLE": "Available (reported)", "BUSY": "Busy (reported)", "OFFLINE": "Offline (reported)"}.get(status, "Unknown")
    return ResourceResponse(
        id=res.id, resource_id=res.id, name=res.name, type=res.resource_type, resource_type=res.resource_type,
        latitude=res.latitude, longitude=res.longitude, lat=res.latitude, lng=res.longitude, address=res.address,
        phone=res.phone if res.verified else None, capabilities=res.capabilities or [],
        availability=label, availability_status=status, availability_verified=verified_av,
        availability_updated_at=av.updated_at.isoformat() if verified_av and av.updated_at else None,
        available_units=av.available_units if verified_av else None,
        distance_km=round(distance_km, 2) if distance_km is not None else None,
        provider={"DEMO_SEED": "Demo seed data (not real)", "OSM": "OpenStreetMap contributors (ODbL), not verified"}.get(
            res.data_source, "RESQ.AI resource registry"),
        data_source=res.data_source, verified=res.verified,
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        navigation_url=f"https://www.google.com/maps/dir/?api=1&destination={res.latitude},{res.longitude}",
    )


class ResourceService:
    @staticmethod
    def nearby_db(db: Session, latitude: float, longitude: float, radius_km: float = 25.0,
                  types: Optional[List[str]] = None, limit: int = 50) -> List[ResourceResponse]:
        sql = text("""
            SELECT id, ST_Distance(geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) / 1000.0 AS km
            FROM emergency_resources
            WHERE geom IS NOT NULL
              AND ST_DWithin(geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :radius_m)
              AND (CAST(:types AS text[]) IS NULL OR resource_type = ANY(CAST(:types AS text[])))
            ORDER BY km ASC LIMIT :lim
        """)
        rows = db.execute(sql, {"lat": latitude, "lng": longitude, "radius_m": radius_km * 1000.0,
                                "types": list(types) if types else None, "lim": limit}).all()
        if not rows:
            return []
        by_id = {r.id: r for r in db.query(EmergencyResource).filter(EmergencyResource.id.in_([x[0] for x in rows])).all()}
        return [_fmt(by_id[rid], km) for rid, km in rows if rid in by_id]

    @staticmethod
    def nearby_osm(latitude: float, longitude: float, radius_km: float, resource_type: Optional[str]) -> List[ResourceResponse]:
        if not settings.ENABLE_OSM_LIVE_LOOKUP:
            return []
        try:
            items = GeospatialDiscoveryService.search_nearby_resources(
                latitude=latitude, longitude=longitude, resource_type=resource_type, radius_km=min(radius_km, 10.0))
        except Exception as e:
            logger.info(f"OSM lookup unavailable: {e}")
            return []
        out = []
        for it in items:
            phone = it.get("phone")
            out.append(ResourceResponse(
                id=it["id"], resource_id=it["id"], name=it["name"], type=it["type"], resource_type=it["type"],
                latitude=it["latitude"], longitude=it["longitude"], lat=it["latitude"], lng=it["longitude"],
                address=it.get("address"), phone=phone if phone and phone != "Not Listed" else None,
                capabilities=it.get("capabilities", []),
                distance_km=GeospatialDiscoveryService.haversine_distance_km(latitude, longitude, it["latitude"], it["longitude"]),
                provider="OpenStreetMap (community data)", data_source="OSM", verified=False,
                retrieved_at=it.get("retrieved_at"), navigation_url=it.get("navigation_url"),
            ))
        return out

    @classmethod
    def get_nearby_resources(cls, db: Session, latitude: float, longitude: float, resource_type: Optional[str] = None,
                             max_radius_km: float = 25.0, include_osm: bool = False) -> List[ResourceResponse]:
        types = [resource_type.upper()] if resource_type else None
        results = cls.nearby_db(db, latitude, longitude, max_radius_km, types)
        if include_osm:
            seen = {(round(r.latitude, 3), round(r.longitude, 3)) for r in results}
            for r in cls.nearby_osm(latitude, longitude, max_radius_km, resource_type):
                if (round(r.latitude, 3), round(r.longitude, 3)) not in seen:
                    results.append(r)
        results.sort(key=lambda r: r.distance_km if r.distance_km is not None else 9e9)
        return results

    @classmethod
    def rank_resources(cls, db: Session, latitude: float, longitude: float, emergency_type: str,
                       injuries: int = 0, affected_people: int = 0, max_radius_km: float = 25.0) -> List[ResourceResponse]:
        """Transparent ranking: relevance of type to category, then straight-line distance.
        Unverified availability is never treated as available."""
        if latitude is None or longitude is None:
            return []
        cat = normalize_category(emergency_type) or "other"
        wanted = TYPES_FOR_CATEGORY.get(cat)
        res = cls.nearby_db(db, latitude, longitude, max_radius_km, list(wanted) if wanted else None)
        for r in res:
            dist_score = max(0.0, 100.0 - (r.distance_km or max_radius_km) / max_radius_km * 100.0)
            type_score = 100.0 if wanted and r.type == wanted[0] else (70.0 if wanted and r.type in wanted else 40.0)
            avail = {"AVAILABLE": 100.0, "BUSY": 20.0, "OFFLINE": 0.0}.get(r.availability_status, 50.0)
            r.suitability_score = round(0.5 * dist_score + 0.3 * type_score + 0.2 * avail, 1)
        res.sort(key=lambda r: r.suitability_score or 0, reverse=True)
        for i, r in enumerate(res):
            r.ranking = i + 1
        return res
