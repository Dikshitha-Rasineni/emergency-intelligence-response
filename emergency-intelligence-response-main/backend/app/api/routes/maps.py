"""
Amazon Location Service map proxy endpoints.

The browser cannot call Amazon Location directly without an API key.
Since API key creation is restricted in this account, the backend proxies
all map asset requests using its IAM credentials.

Routes:
  GET /api/v1/maps/style.json          — MapLibre style descriptor
  GET /api/v1/maps/tiles/{z}/{x}/{y}   — Vector map tiles
  GET /api/v1/maps/glyphs/{font_stack}/{range}.pbf  — Text glyphs
  GET /api/v1/maps/sprites/{filename}  — Icon sprites
"""

from fastapi import APIRouter, HTTPException, Response
from app.services.location_service import LocationService
from app.core.config import settings

router = APIRouter()


@router.get("/maps/style.json")
def get_map_style():
    """Proxy the MapLibre style descriptor from Amazon Location."""
    if not settings.AWS_LOCATION_MAP_NAME:
        raise HTTPException(status_code=503, detail={
            "error": "MAP_NOT_CONFIGURED",
            "message": "AWS_LOCATION_MAP_NAME is not configured."
        })
    data = LocationService.get_map_style_descriptor()
    if data is None:
        raise HTTPException(status_code=503, detail={
            "error": "MAP_UNAVAILABLE",
            "message": "Map style descriptor is temporarily unavailable."
        })
    # Rewrite tile URLs in the style to point to our proxy
    import json
    style = json.loads(data)
    base = f"/api/v1/maps"
    if "sources" in style:
        for src in style["sources"].values():
            if "tiles" in src:
                src["tiles"] = [f"{base}/tiles/{{z}}/{{x}}/{{y}}"]
    if "glyphs" in style:
        style["glyphs"] = f"{base}/glyphs/{{fontstack}}/{{range}}.pbf"
    if "sprite" in style:
        style["sprite"] = f"{base}/sprites/sprites"
    return Response(content=json.dumps(style), media_type="application/json")


@router.get("/maps/tiles/{z}/{x}/{y}")
def get_map_tile(z: int, x: int, y: int):
    """Proxy vector map tile from Amazon Location."""
    if not settings.AWS_LOCATION_MAP_NAME:
        raise HTTPException(status_code=503, detail={"error": "MAP_NOT_CONFIGURED"})
    data = LocationService.get_map_tile(z, x, y)
    if data is None:
        raise HTTPException(status_code=503, detail={"error": "TILE_UNAVAILABLE"})
    return Response(
        content=data,
        media_type="application/vnd.mapbox-vector-tile",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/maps/glyphs/{font_stack}/{font_range}.pbf")
def get_map_glyphs(font_stack: str, font_range: str):
    """Proxy map glyphs from Amazon Location."""
    if not settings.AWS_LOCATION_MAP_NAME:
        raise HTTPException(status_code=503, detail={"error": "MAP_NOT_CONFIGURED"})
    data = LocationService.get_map_glyphs(font_stack, f"{font_range}.pbf")
    if data is None:
        raise HTTPException(status_code=503, detail={"error": "GLYPHS_UNAVAILABLE"})
    return Response(content=data, media_type="application/x-protobuf")


@router.get("/maps/sprites/{filename}")
def get_map_sprites(filename: str):
    """Proxy map sprites from Amazon Location."""
    if not settings.AWS_LOCATION_MAP_NAME:
        raise HTTPException(status_code=503, detail={"error": "MAP_NOT_CONFIGURED"})
    data = LocationService.get_map_sprites(filename)
    if data is None:
        raise HTTPException(status_code=503, detail={"error": "SPRITES_UNAVAILABLE"})
    media = "image/png" if filename.endswith(".png") else "application/json"
    return Response(content=data, media_type=media)
