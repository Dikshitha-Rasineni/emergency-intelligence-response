"""
IoT ingestion. Rules:
- Every reading is stored (telemetry history), keyed by event_id for idempotency.
- Only non-simulated, alert_qualified events of a known emergency type can create or join an incident.
- event_type alone never triggers an incident (fixes the earlier false-accident path).
- Qualified alerts merge into a nearby open incident instead of creating a duplicate.
- The response is the delivery acknowledgement the firmware waits for.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.sensor import SensorReading, Device
from app.schemas.iot import IoTEventCreate, IoTEventResponse
from app.services.audit_service import AuditService

EVENT_CATEGORY = {"ACCIDENT": "road_accident", "FIRE": "fire", "GAS": "gas_leak", "FLOOD": "flood", "SOS": "sos"}
_READING_FIELDS = (
    "device_id", "event_id", "transport", "temperature", "smoke_level", "water_level", "impact",
    "acceleration_magnitude_g", "alert_qualified", "simulated", "firmware_version", "wifi_connected", "uptime_ms",
    "mpu6050_available", "dht22_available", "mq2_available", "mq2_warmed", "mq2_calibrated", "humidity_percent",
    "mq2_raw_adc", "mq2_filtered_adc", "mq2_baseline_adc", "acceleration_magnitude_mps2", "dynamic_acceleration_g",
    "vibration_rms_g", "gyro_x_dps", "gyro_y_dps", "gyro_z_dps", "hazard_severity", "source_sensor",
    "observed_value", "threshold_value", "measurement_unit", "reason", "water_level_raw_adc", "fsr_raw_adc", "signal_quality",
)


class IoTService:
    @staticmethod
    def _ack(reading: SensorReading, status: str, message: str, priority=None, severity=None) -> IoTEventResponse:
        return IoTEventResponse(reading_id=reading.id, device_id=reading.device_id, event_type=reading.event_type,
                                event_id=reading.event_id, status=status, incident_id=reading.incident_id,
                                priority_score=priority, severity=severity, message=message)

    @classmethod
    def ingest_sensor_event(cls, db: Session, event: IoTEventCreate) -> IoTEventResponse:
        from app.services.incident_service import IncidentService
        if event.event_id:
            existing = db.query(SensorReading).filter_by(event_id=event.event_id).first()
            if existing:
                return cls._ack(existing, "DUPLICATE", "Event already received; no new incident created.")

        device = db.get(Device, event.device_id)
        now = datetime.now(timezone.utc)
        if not device:
            device = Device(device_id=event.device_id, name=event.device_id, active=True)
            db.add(device)
        if event.firmware_version != "console-demo":  # "online" must reflect real hardware check-ins only
            device.last_seen_at, device.firmware_version, device.last_transport = now, event.firmware_version, event.transport
            if event.signal_quality is not None:
                device.last_signal_quality = event.signal_quality

        lat, lng = event.latitude, event.longitude
        if (lat is None or lng is None) and device.latitude is not None:
            lat, lng = device.latitude, device.longitude

        reading = SensorReading(**{k: getattr(event, k) for k in _READING_FIELDS}, event_type=event.event_type,
                                latitude=lat, longitude=lng, device_timestamp=event.timestamp, timestamp=now)
        db.add(reading)
        try:
            db.flush()
        except IntegrityError:  # concurrent retry with the same event_id
            db.rollback()
            existing = db.query(SensorReading).filter_by(event_id=event.event_id).first()
            return cls._ack(existing, "DUPLICATE", "Event already received; no new incident created.")

        category = EVENT_CATEGORY.get(event.event_type.upper())
        qualifies = bool(category) and event.alert_qualified and not event.simulated
        if not qualifies:
            db.commit()
            why = "simulated data" if event.simulated else ("telemetry" if not category else "alert not qualified by device rules")
            return cls._ack(reading, "STORED", f"Reading stored ({why}); no incident created.")
        if lat is None or lng is None:
            db.commit()
            return cls._ack(reading, "REJECTED_NO_LOCATION",
                            "Qualified alert stored but no incident created: device has no registered location.")

        label = device.location_label or device.name or f"Sensor {device.device_id}"
        inc, merged = IncidentService.create_from_iot(db, reading, category, label)
        reading.created_incident = not merged
        AuditService.record(db, f"device:{event.device_id}", "iot.alert", "incident", inc.id,
                            {"event_id": event.event_id, "event_type": event.event_type, "merged": merged})
        db.commit()
        db.expire_all()  # reload the newest assessment for the acknowledgement
        db.refresh(inc)
        IncidentService.push_updates(db, inc)
        ass = inc.severity_assessments[0] if inc.severity_assessments else None
        return cls._ack(reading, "MERGED_INTO_INCIDENT" if merged else "INCIDENT_CREATED",
                        f"Qualified sensor alert {'attached to' if merged else 'created'} incident {inc.id}.",
                        int(ass.priority_score) if ass else None, ass.severity if ass else None)
