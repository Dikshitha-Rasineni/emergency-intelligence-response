from fastapi import APIRouter, Query
from typing import Optional
from app.schemas.routing import RouteRequest, RouteResponse
from app.services.routing_service import RoutingService

router = APIRouter()


@router.get("/routes", response_model=RouteResponse)
def get_route(
    origin_lat: float = Query(..., ge=-90.0, le=90.0),
    origin_lng: float = Query(..., ge=-180.0, le=180.0),
    destination_lat: float = Query(..., ge=-90.0, le=90.0),
    destination_lng: float = Query(..., ge=-180.0, le=180.0),
    origin_name: Optional[str] = Query("Station Base"),
    destination_name: Optional[str] = Query("Incident Location"),
    responder_role: Optional[str] = Query(None),
):
    """
    Computes verified routing metrics, road distance, ETA, waypoints, and navigation steps.
    """
    return RoutingService.calculate_route(
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        destination_lat=destination_lat,
        destination_lng=destination_lng,
        origin_name=origin_name,
        destination_name=destination_name,
        responder_role=responder_role,
    )


@router.post("/routes", response_model=RouteResponse)
def calculate_route_post(req: RouteRequest):
    """
    POST variant of route calculation.
    """
    return RoutingService.calculate_route(
        origin_lat=req.origin_lat,
        origin_lng=req.origin_lng,
        destination_lat=req.destination_lat,
        destination_lng=req.destination_lng,
        origin_name=req.origin_name or "Station Base",
        destination_name=req.destination_name or "Incident Location",
        responder_role=req.responder_role,
    )
