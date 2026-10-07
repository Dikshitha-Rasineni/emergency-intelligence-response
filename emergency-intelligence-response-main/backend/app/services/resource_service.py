from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.resource import EmergencyResource, ResourceAvailability
from app.schemas.resource import ResourceResponse
from app.services.routing_service import RoutingService


class ResourceService:
    @staticmethod
    def _format_resource(res: EmergencyResource, distance_km: float = None, eta_min: int = None, score: float = None, ranking: int = None) -> ResourceResponse:
        avail_str = "Unavailable"
        avail_units = 0
        wait_time = 0
        details = {}

        if res.availability:
            avail_units = res.availability.available_units
            wait_time = res.availability.wait_time
            details = res.availability.operational_details or {}
            
            # Format human-readable availability
            if res.resource_type == "HOSPITAL":
                avail_str = details.get("emergency_dept", f"{avail_units} Beds Available" if res.availability.status == "AVAILABLE" else "Busy")
            elif res.resource_type == "AMBULANCE":
                avail_str = "Available on Ramp" if res.availability.status == "AVAILABLE" else "On Dispatch"
            elif res.resource_type == "POLICE":
                avail_str = "Patrol Unit Available" if res.availability.status == "AVAILABLE" else "Busy"
            elif res.resource_type == "FIRE":
                avail_str = "Heavy Rescue Tender Ready" if res.availability.status == "AVAILABLE" else "Standby"
            else:
                avail_str = res.availability.status

        # Capability summary string
        cap_summary = " · ".join(res.capabilities) if res.capabilities else "Emergency Service Ready"

        return ResourceResponse(
            id=res.id,
            resource_id=res.id,
            name=res.name,
            type=res.resource_type,
            resource_type=res.resource_type,
            latitude=res.latitude,
            longitude=res.longitude,
            lat=res.latitude,
            lng=res.longitude,
            address=res.address,
            phone=res.phone,
            contact=res.phone or "112",
            capabilities=res.capabilities or [],
            capability=cap_summary,
            availability=avail_str,
            available_units=avail_units,
            wait_time=wait_time,
            distance_km=distance_km,
            eta_min=eta_min,
            suitability_score=score,
            ranking=ranking,
            operational_details=details,
        )

    @classmethod
    def get_nearby_resources(
        cls,
        db: Session,
        latitude: float,
        longitude: float,
        resource_type: Optional[str] = None,
        max_radius_km: float = 25.0,
    ) -> List[ResourceResponse]:
        """
        Discovers verified nearby emergency resources from the database within radius.
        """
        query = db.query(EmergencyResource)
        if resource_type:
            query = query.filter(EmergencyResource.resource_type == resource_type.upper())

        all_res = query.all()
        results: List[ResourceResponse] = []

        for r in all_res:
            crow_km = RoutingService.haversine_distance_km(latitude, longitude, r.latitude, r.longitude)
            road_km = round(crow_km * 1.25, 1)

            if road_km <= max_radius_km:
                eta_min = max(2, int(round((road_km / 40.0) * 60.0 + 1)))
                formatted = cls._format_resource(r, distance_km=road_km, eta_min=eta_min)
                results.append(formatted)

        # Sort by distance
        results.sort(key=lambda x: x.distance_km or 999.0)
        return results

    @classmethod
    def rank_resources(
        cls,
        db: Session,
        latitude: float,
        longitude: float,
        emergency_type: str,
        injuries: int = 0,
        affected_people: int = 0,
        max_radius_km: float = 25.0,
    ) -> List[ResourceResponse]:
        """
        Multi-factor resource ranking considering:
        - Proximity & ETA (40%)
        - Real availability & capacity (30%)
        - Capability suitability to emergency type (30%)
        """
        nearby = cls.get_nearby_resources(db, latitude, longitude, max_radius_km=max_radius_km)
        type_lower = emergency_type.lower()

        ranked: List[ResourceResponse] = []
        for r in nearby:
            # 1. Distance score (100 for <= 1km, degrading to 0 at 25km)
            dist = r.distance_km or 10.0
            dist_score = max(0.0, 100.0 - (dist / 25.0) * 100.0)

            # 2. Availability score
            avail_score = 100.0 if "Available" in r.availability or "Ready" in r.availability else 40.0
            if r.available_units > 1:
                avail_score = min(100.0, avail_score + 10.0)

            # 3. Domain suitability score
            suitability = 50.0
            if "accident" in type_lower or "crash" in type_lower:
                if r.type in ["HOSPITAL", "AMBULANCE"]:
                    suitability = 95.0
                elif r.type == "POLICE":
                    suitability = 90.0
                elif r.type == "FIRE":
                    suitability = 70.0
            elif "fire" in type_lower or "smoke" in type_lower:
                if r.type == "FIRE":
                    suitability = 100.0
                elif r.type in ["AMBULANCE", "HOSPITAL"]:
                    suitability = 85.0
                elif r.type == "POLICE":
                    suitability = 80.0
            elif "flood" in type_lower or "water" in type_lower:
                if r.type == "FIRE":
                    suitability = 95.0
                elif r.type == "POLICE":
                    suitability = 85.0
                else:
                    suitability = 60.0
            elif "cardiac" in type_lower or "medical" in type_lower:
                if r.type in ["AMBULANCE", "HOSPITAL"]:
                    suitability = 100.0
                else:
                    suitability = 40.0

            # Composite multi-factor score
            final_score = round(dist_score * 0.40 + avail_score * 0.30 + suitability * 0.30, 1)
            r.suitability_score = final_score
            ranked.append(r)

        ranked.sort(key=lambda x: x.suitability_score or 0.0, reverse=True)
        for idx, item in enumerate(ranked):
            item.ranking = idx + 1

        return ranked
