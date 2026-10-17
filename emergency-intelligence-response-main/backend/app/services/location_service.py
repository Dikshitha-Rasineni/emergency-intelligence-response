"""
Amazon Location Service integration for RESQ.AI.

Responsibilities:
  - Route calculation via Amazon Location Routes (geo:CalculateRoute)
  - Map tile proxy (geo:GetMapTile, geo:GetMapStyleDescriptor, geo:GetMapSprites, geo:GetMapGlyphs)

Does NOT:
  - Calculate priority or severity
  - Fabricate distances or ETAs
  - Replace PostGIS spatial filtering (that stays in ResourceService)
"""

import boto3
import logging
from typing import Optional
from botocore.exceptions import ClientError, EndpointResolutionError, NoCredentialsError

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_location_client():
    """Return a boto3 Amazon Location Service client using configured region."""
    return boto3.client("location", region_name=settings.AWS_REGION)


class LocationService:
    """Amazon Location Service — routing and map tile proxy."""

    # -------------------------------------------------------------------------
    # ROUTING
    # -------------------------------------------------------------------------

    @classmethod
    def calculate_route(
        cls,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        travel_mode: str = "Car",
    ) -> Optional[dict]:
        """
        Call Amazon Location Routes (geo:CalculateRoute).

        Returns a normalized dict:
          distance_meters  int
          duration_seconds int
          geometry         list[list[float]]  [[lat, lng], ...]  Leaflet-compatible
          travel_mode      str
          source           str  "AMAZON_LOCATION"

        Returns None on any failure so the caller can fall back to OSRM.
        """
        if not settings.AWS_LOCATION_ROUTE_CALCULATOR:
            logger.debug("AWS_LOCATION_ROUTE_CALCULATOR not configured — skipping Amazon Location routing.")
            return None

        try:
            client = _get_location_client()
            response = client.calculate_route(
                CalculatorName=settings.AWS_LOCATION_ROUTE_CALCULATOR,
                DeparturePosition=[origin_lng, origin_lat],   # Amazon Location: [lng, lat]
                DestinationPosition=[dest_lng, dest_lat],
                TravelMode=travel_mode,
                IncludeLegGeometry=True,
            )

            legs = response.get("Legs", [])
            if not legs:
                logger.warning("Amazon Location returned no route legs.")
                return None

            leg = legs[0]
            summary = response.get("Summary", {})

            distance_m = int(summary.get("Distance", 0) * 1000)   # km → m
            duration_s = int(summary.get("DurationSeconds", 0))

            # Geometry: Amazon Location returns [lng, lat] — convert to Leaflet [lat, lng]
            geometry_positions = leg.get("Geometry", {}).get("LineString", [])
            leaflet_coords = [[round(p[1], 5), round(p[0], 5)] for p in geometry_positions]

            if not leaflet_coords:
                logger.warning("Amazon Location route has no geometry.")
                return None

            return {
                "distance_meters": distance_m,
                "duration_seconds": duration_s,
                "geometry": leaflet_coords,
                "travel_mode": travel_mode,
                "source": "AMAZON_LOCATION",
            }

        except NoCredentialsError:
            logger.error("AWS credentials not found — cannot call Amazon Location Routes.")
        except ClientError as e:
            code = e.response["Error"]["Code"]
            logger.warning(f"Amazon Location ClientError [{code}]: {e.response['Error']['Message']}")
        except EndpointResolutionError as e:
            logger.warning(f"Amazon Location endpoint error: {e}")
        except Exception as e:
            logger.warning(f"Amazon Location routing unexpected error: {e}")

        return None

    # -------------------------------------------------------------------------
    # MAP TILE PROXY
    # -------------------------------------------------------------------------

    @classmethod
    def get_map_style_descriptor(cls) -> Optional[bytes]:
        """Fetch the MapLibre style JSON for the configured map resource."""
        if not settings.AWS_LOCATION_MAP_NAME:
            return None
        try:
            client = _get_location_client()
            resp = client.get_map_style_descriptor(MapName=settings.AWS_LOCATION_MAP_NAME)
            return resp["Blob"].read()
        except Exception as e:
            logger.warning(f"get_map_style_descriptor error: {e}")
            return None

    @classmethod
    def get_map_glyphs(cls, font_stack: str, font_unicode_range: str) -> Optional[bytes]:
        """Proxy map glyph requests for MapLibre text rendering."""
        if not settings.AWS_LOCATION_MAP_NAME:
            return None
        try:
            client = _get_location_client()
            resp = client.get_map_glyphs(
                MapName=settings.AWS_LOCATION_MAP_NAME,
                FontStack=font_stack,
                FontUnicodeRange=font_unicode_range,
            )
            return resp["Blob"].read()
        except Exception as e:
            logger.warning(f"get_map_glyphs error: {e}")
            return None

    @classmethod
    def get_map_sprites(cls, filename: str) -> Optional[bytes]:
        """Proxy map sprite requests for MapLibre icon rendering."""
        if not settings.AWS_LOCATION_MAP_NAME:
            return None
        try:
            client = _get_location_client()
            resp = client.get_map_sprites(
                MapName=settings.AWS_LOCATION_MAP_NAME,
                FileName=filename,
            )
            return resp["Blob"].read()
        except Exception as e:
            logger.warning(f"get_map_sprites error: {e}")
            return None

    @classmethod
    def get_map_tile(cls, z: int, x: int, y: int) -> Optional[bytes]:
        """Proxy vector map tile requests for MapLibre rendering."""
        if not settings.AWS_LOCATION_MAP_NAME:
            return None
        try:
            client = _get_location_client()
            resp = client.get_map_tile(
                MapName=settings.AWS_LOCATION_MAP_NAME,
                Z=str(z),
                X=str(x),
                Y=str(y),
            )
            return resp["Blob"].read()
        except Exception as e:
            logger.warning(f"get_map_tile error: {e}")
            return None
