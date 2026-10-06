from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.resource import ResourceResponse

router = APIRouter()


@router.get("/resources/nearby", response_model=list[ResourceResponse])
def get_nearby_resources(
    incident_id: str = Query(...),
    radius_km: float = Query(default=25.0, gt=0),
    db: Session = Depends(get_db),
):
    incident = db.execute(
        text(
            """
            SELECT id, latitude, longitude
            FROM emergency_reports
            WHERE id = :incident_id
            """
        ),
        {"incident_id": incident_id},
    ).mappings().first()

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    query = text(
        """
        SELECT
            r.id,
            r.name,
            r.resource_type,
            r.latitude,
            r.longitude,
            r.address,
            r.contact_number,

            COALESCE(a.available_units, 0) AS available_units,
            COALESCE(a.status, 'unknown') AS availability_status,
            COALESCE(a.wait_time_minutes, 0) AS wait_time_minutes,

            ROUND(
                (
                    ST_Distance(
                        r.location_geog,
                        ST_SetSRID(
                            ST_MakePoint(
                                :incident_longitude,
                                :incident_latitude
                            ),
                            4326
                        )::geography
                    ) / 1000.0
                )::numeric,
                2
            )::float AS distance_km

        FROM emergency_resources r

        LEFT JOIN resource_availability a
            ON a.resource_id = r.id

        WHERE ST_DWithin(
            r.location_geog,
            ST_SetSRID(
                ST_MakePoint(
                    :incident_longitude,
                    :incident_latitude
                ),
                4326
            )::geography,
            :radius_meters
        )

        ORDER BY distance_km ASC
        """
    )

    radius_meters = radius_km * 1000

    resources = db.execute(
        query,
        {
            "incident_longitude": incident["longitude"],
            "incident_latitude": incident["latitude"],
            "radius_meters": radius_meters,
        },
    ).mappings().all()

    return [
        ResourceResponse(
            id=resource["id"],
            name=resource["name"],
            resource_type=resource["resource_type"],
            latitude=resource["latitude"],
            longitude=resource["longitude"],
            address=resource["address"],
            contact_number=resource["contact_number"],
            available_units=resource["available_units"],
            availability_status=resource["availability_status"],
            wait_time_minutes=resource["wait_time_minutes"],
            distance_km=resource["distance_km"],
        )
        for resource in resources
    ]