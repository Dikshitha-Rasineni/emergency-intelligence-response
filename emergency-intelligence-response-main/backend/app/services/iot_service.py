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
            acceleration_magnitude_g=event.acceleration_magnitude_g,
            alert_qualified=event.alert_qualified,
            simulated=event.simulated,
            firmware_version=event.firmware_version,
            wifi_connected=event.wifi_connected,
            uptime_ms=event.uptime_ms,
            mpu6050_available=event.mpu6050_available,
            dht22_available=event.dht22_available,
            mq2_available=event.mq2_available,
            mq2_warmed=event.mq2_warmed,
            mq2_calibrated=event.mq2_calibrated,
            humidity_percent=event.humidity_percent,
            mq2_raw_adc=event.mq2_raw_adc,
            mq2_filtered_adc=event.mq2_filtered_adc,
            mq2_baseline_adc=event.mq2_baseline_adc,
            acceleration_magnitude_mps2=event.acceleration_magnitude_mps2,
            dynamic_acceleration_g=event.dynamic_acceleration_g,
            vibration_rms_g=event.vibration_rms_g,
            gyro_x_dps=event.gyro_x_dps,
            gyro_y_dps=event.gyro_y_dps,
            gyro_z_dps=event.gyro_z_dps,
            hazard_severity=event.hazard_severity,
            source_sensor=event.source_sensor,
            observed_value=event.observed_value,
            threshold_value=event.threshold_value,
            measurement_unit=event.measurement_unit,
            reason=event.reason,
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

        # Do not promote a single noisy sample from routine telemetry to an incident.
        # Firmware sets alert_qualified only after the configured persistence rules pass.
        is_accident = not event.simulated and (
            event.event_type.upper() == "ACCIDENT"
            or (event.alert_qualified and event.impact is not None and event.impact >= 5.0)
        )
        is_fire = not event.simulated and (
            event.event_type.upper() == "FIRE"
            or (
                event.alert_qualified
                and ((event.smoke_level is not None and event.smoke_level >= 1500.0)
                     or (event.temperature is not None and event.temperature >= 60.0))
            )
        )
        is_flood = not event.simulated and (
            event.event_type.upper() == "FLOOD"
            or (event.alert_qualified and event.water_level is not None and event.water_level >= 50.0)
        )

        if is_accident or is_fire or is_flood:
            if event.source_sensor and event.observed_value is not None:
                unit = event.measurement_unit or ""
                threshold = f"; configured threshold {event.threshold_value} {unit}" if event.threshold_value is not None else ""
                desc = (f"Preliminary sensor observation [{event.device_id}]: {event.reason or 'threshold condition'}; "
                        f"sensor={event.source_sensor}, observed={event.observed_value} {unit}{threshold}, "
                        f"reported severity={event.hazard_severity or 'critical'}; location={event.latitude}, {event.longitude}.")
            elif is_accident:
                desc = f"ESP32 telemetry alert [{event.device_id}]: High impact deceleration detected ({event.impact}G) at coordinates {event.latitude}, {event.longitude}."
                etype = "Major Road Accident"
            elif is_fire:
                desc = f"ESP32 telemetry alert [{event.device_id}]: Hazardous smoke level ({event.smoke_level} ppm) and high temperature ({event.temperature}°C)."
                etype = "Commercial Building Fire"
            else:
                desc = f"ESP32 telemetry alert [{event.device_id}]: Critical water surge detected ({event.water_level} cm) in underpass/corridor."
                etype = "Urban Flash Flood & Vehicle Stall"
            if is_accident:
                etype = "Major Road Accident"
            elif is_fire:
                etype = "Commercial Building Fire"
            elif is_flood:
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
