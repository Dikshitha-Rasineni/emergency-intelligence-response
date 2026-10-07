from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.sensor import SensorReading
from app.schemas.iot import IoTEventCreate, IoTEventResponse
from app.schemas.incident import IncidentCreate
from app.services.incident_service import IncidentService


class IoTService:
    @classmethod
    def ingest_sensor_event(cls, db: Session, event: IoTEventCreate) -> IoTEventResponse:
        # 1. Record sensor telemetry
        reading = SensorReading(
            device_id=event.device_id,
            event_type=event.event_type,
            temperature=event.temperature,
            smoke_level=event.smoke_level,
            water_level=event.water_level,
            impact=event.impact,
            latitude=event.latitude,
            longitude=event.longitude,
            timestamp=event.timestamp or datetime.now(timezone.utc),
        )
        db.add(reading)
        db.flush()

        incident_id = None
        priority_score = None
        severity = None
        message = "Sensor telemetry recorded successfully."

        # 2. Automated Critical Threshold Evaluation
        is_accident = (event.impact is not None and event.impact >= 5.0) or event.event_type.upper() == "ACCIDENT"
        is_fire = (event.smoke_level is not None and event.smoke_level >= 1500.0) or (event.temperature is not None and event.temperature >= 60.0) or event.event_type.upper() == "FIRE"
        is_flood = (event.water_level is not None and event.water_level >= 50.0) or event.event_type.upper() == "FLOOD"

        if is_accident or is_fire or is_flood:
            if is_accident:
                desc = f"ESP32 telemetry alert [{event.device_id}]: High impact deceleration detected ({event.impact}G) at coordinates {event.latitude}, {event.longitude}."
                etype = "Major Road Accident"
            elif is_fire:
                desc = f"ESP32 telemetry alert [{event.device_id}]: Hazardous smoke level ({event.smoke_level} ppm) and high temperature ({event.temperature}°C)."
                etype = "Commercial Building Fire"
            else:
                desc = f"ESP32 telemetry alert [{event.device_id}]: Critical water surge detected ({event.water_level} cm) in underpass/corridor."
                etype = "Urban Flash Flood & Vehicle Stall"

            inc_create = IncidentCreate(
                description=desc,
                latitude=event.latitude,
                longitude=event.longitude,
                location=f"ESP32 Automated Sensor Station #{event.device_id}",
                affected_people=1,
                injuries=0,
                emergency_type=etype,
                source="IOT",
            )
            created_inc = IncidentService.create_incident(db, inc_create)
            reading.incident_id = created_inc.incident_id
            incident_id = created_inc.incident_id
            priority_score = created_inc.priority_score
            severity = created_inc.severity
            message = f"Critical sensor alert triggered new incident {incident_id} ({severity} priority)."

        db.commit()

        return IoTEventResponse(
            reading_id=reading.id,
            device_id=reading.device_id,
            event_type=reading.event_type,
            status="PROCESSED",
            incident_id=incident_id,
            priority_score=priority_score,
            severity=severity,
            message=message,
        )
