from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.resource import ResourceResponse, ResourceRankRequest, ResourceRankResponse
from app.services.resource_service import ResourceService

router = APIRouter()


@router.get("/resources/nearby", response_model=List[ResourceResponse])
def get_nearby_resources(latitude: float = Query(..., ge=-90.0, le=90.0), longitude: float = Query(..., ge=-180.0, le=180.0),
                         type: Optional[str] = Query(None, pattern="^(HOSPITAL|AMBULANCE|POLICE|FIRE|SHELTER|DISASTER)$"),
                         radius: float = Query(10.0, ge=0.5, le=50.0),
                         include_osm: bool = Query(False, description="Also query OpenStreetMap live (community data)"),
                         db: Session = Depends(get_db)):
    """Nearby facilities via PostGIS. Distances are straight-line; availability is UNKNOWN unless reported."""
    return ResourceService.get_nearby_resources(db, latitude, longitude, type, radius, include_osm=include_osm)


@router.post("/resources/rank", response_model=ResourceRankResponse)
def rank_resources(req: ResourceRankRequest, db: Session = Depends(get_db)):
    ranked = ResourceService.rank_resources(db, req.latitude, req.longitude, req.emergency_type, req.injuries,
                                            req.affected_people, req.max_radius_km)
    return ResourceRankResponse(total_found=len(ranked), resources=ranked)


@router.get("/resources/geocode")
def geocode_location(query: str = Query(..., min_length=2, max_length=255)):
    from app.services.geospatial_discovery_service import GeospatialDiscoveryService
    res = GeospatialDiscoveryService.geocode_location(query)
    if not res:
        return {"found": False, "query": query, "message": "Location could not be found."}
    lat, lng, display = res
    return {"found": True, "query": query, "latitude": lat, "longitude": lng, "display_name": display,
            "provider": "OpenStreetMap Nominatim", "approximate": True}
