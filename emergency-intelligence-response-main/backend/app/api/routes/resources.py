from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.resource import ResourceResponse, ResourceRankRequest, ResourceRankResponse
from app.services.resource_service import ResourceService

router = APIRouter()


@router.get("/resources", response_model=List[ResourceResponse])
def get_all_resources(
    resource_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns verified emergency resources registry.
    """
    # Use center of operations (Bengaluru city center 12.9716, 77.5946) to query all in area
    return ResourceService.get_nearby_resources(
        db,
        latitude=12.9716,
        longitude=77.5946,
        resource_type=resource_type,
        max_radius_km=50.0,
    )


@router.get("/resources/nearby", response_model=List[ResourceResponse])
def get_nearby_resources(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    type: Optional[str] = Query(None, description="Resource type filter: HOSPITAL, AMBULANCE, POLICE, FIRE"),
    radius: float = Query(25.0, ge=0.5, le=100.0, description="Search radius in kilometers"),
    db: Session = Depends(get_db),
):
    """
    Finds real, verified nearby emergency facilities, ambulances, police, and fire tenders.
    """
    return ResourceService.get_nearby_resources(
        db=db,
        latitude=latitude,
        longitude=longitude,
        resource_type=type,
        max_radius_km=radius,
    )


@router.post("/resources/rank", response_model=ResourceRankResponse)
def rank_resources(
    rank_req: ResourceRankRequest,
    db: Session = Depends(get_db),
):
    """
    Calculates multi-factor resource ranking considering proximity, ETA, capacity, and emergency match.
    """
    ranked = ResourceService.rank_resources(
        db=db,
        latitude=rank_req.latitude,
        longitude=rank_req.longitude,
        emergency_type=rank_req.emergency_type,
        injuries=rank_req.injuries,
        affected_people=rank_req.affected_people,
        max_radius_km=rank_req.max_radius_km,
    )
    return ResourceRankResponse(
        total_found=len(ranked),
        resources=ranked,
    )


@router.get("/resources/geocode")
def geocode_location(query: str = Query(..., min_length=2)):
    """
    Geocodes an address or landmark to latitude, longitude, and formatted name.
    """
    from app.services.geospatial_discovery_service import GeospatialDiscoveryService
    res = GeospatialDiscoveryService.geocode_location(query)
    if not res:
        return {"found": False, "query": query, "message": "Location could not be verified."}
    lat, lng, display = res
    return {"found": True, "query": query, "latitude": lat, "longitude": lng, "display_name": display}
