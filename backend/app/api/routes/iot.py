from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import verify_device
from app.db.session import get_db
from app.schemas.iot import IoTEventCreate, IoTEventResponse
from app.services.iot_service import IoTService

router = APIRouter()


def _prewarm(background: BackgroundTasks, ack) -> None:
    """Sensor alerts have no human text: GenAI writes the first account of the incident for each service."""
    inc = getattr(ack, "incident_id", None)
    if inc and ack.status != "DUPLICATE":
        from app.services.genai_service import prewarm
        background.add_task(prewarm, inc)


@router.post("/iot/events", response_model=IoTEventResponse, status_code=201, dependencies=[Depends(verify_device)])
def ingest_iot_sensor_event(event: IoTEventCreate, background: BackgroundTasks, db: Session = Depends(get_db)):
    """ESP32 telemetry and qualified alerts. 201 = stored; 200 = duplicate event_id (already stored).
    The firmware treats any 2xx with a reading_id as a delivery acknowledgement."""
    ack = IoTService.ingest_sensor_event(db, event)
    _prewarm(background, ack)
    if ack.status == "DUPLICATE":
        return JSONResponse(status_code=200, content=ack.model_dump())
    return ack


# ---------------------------------------------------------------------------
# SIM800L-friendly endpoint: short form fields, token in the body (AT+HTTP headers are awkward on GSM modules)
# ---------------------------------------------------------------------------
from fastapi import Request


@router.post("/iot/sim", status_code=201)
async def ingest_sim(request: Request, background: BackgroundTasks, db: Session = Depends(get_db)):
    """For the in-car unit sending over a SIM card. Accepts form-encoded or JSON with short keys:
    id (device), e (event id), ty (crash|hb), f (force, N), t (threshold, N), raw (FSR ADC 0-4095),
    lat, lng (optional; else the registered location), csq (AT+CSQ), fw (firmware), k (device token).
    Replies with a short plain-text line the ESP32 can parse: "OK <reading_id> <incident_id|->"."""
    from fastapi.responses import PlainTextResponse
    ctype = request.headers.get("content-type", "")
    raw = await request.json() if "json" in ctype else dict(await request.form())
    if not raw:
        raw = dict(request.query_params)
    expected = settings.IOT_DEVICE_TOKEN
    if expected and str(raw.get("k", "")) != expected and request.headers.get("authorization", "") != f"Bearer {expected}":
        return PlainTextResponse("ERR token", status_code=401)

    def num(key, cast=float):
        try:
            return cast(raw[key]) if raw.get(key) not in (None, "") else None
        except (TypeError, ValueError):
            return None
    crash = str(raw.get("ty", "crash")).lower() in ("crash", "accident", "1")
    f, t = num("f"), num("t")
    try:
        ev = IoTEventCreate(
            device_id=str(raw.get("id", "")), event_id=str(raw.get("e") or "") or None,
            event_type="ACCIDENT" if crash else "TELEMETRY", alert_qualified=crash, transport="GPRS",
            fsr_raw_adc=num("raw", int), observed_value=f, threshold_value=t, measurement_unit="N" if f is not None else None,
            source_sensor="fsr", signal_quality=num("csq", int), firmware_version=(str(raw.get("fw"))[:32] if raw.get("fw") else None),
            hazard_severity=("CRITICAL" if f and t and f >= 1.5 * t else "HIGH") if crash else None,
            reason="Crash force on the in-car sensor above the limit" if crash else None,
            latitude=num("lat"), longitude=num("lng"))
    except Exception as exc:  # validation error -> short reply the firmware can log
        return PlainTextResponse(f"ERR {str(exc)[:120]}", status_code=422)
    ack = IoTService.ingest_sensor_event(db, ev)
    _prewarm(background, ack)
    return PlainTextResponse(f"OK {ack.reading_id} {ack.incident_id or '-'} {ack.status}",
                             status_code=200 if ack.status == "DUPLICATE" else 201)


# ---------------------------------------------------------------------------
# Sensor network view + demo trigger (control-room side)
# ---------------------------------------------------------------------------
import uuid
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel

from app.api.deps import require_roles, CONTROL_ROOM_ROLES
from app.core.config import settings
from app.models.sensor import Device, SensorReading
from app.models.user import User
from app.services.audit_service import AuditService

_DEMO_READINGS = {
    # In-car force (pressure) sensor read by the ESP32, sent over the SIM800L: same fields the real unit sends.
    "ACCIDENT": dict(fsr_raw_adc=3350, hazard_severity="CRITICAL", source_sensor="fsr", observed_value=62.0,
                     threshold_value=40.0, measurement_unit="N", signal_quality=18,
                     reason="Crash force on the in-car sensor above the limit"),
    "FIRE": dict(temperature=74.0, humidity_percent=21.0, mq2_raw_adc=2950, mq2_baseline_adc=1200, hazard_severity="HIGH",
                 source_sensor="dht22+mq2_analog", observed_value=74.0, threshold_value=55.0, measurement_unit="degC",
                 reason="Smoke and rapid heat rise detected"),
    "GAS": dict(mq2_raw_adc=2150, mq2_baseline_adc=1200, hazard_severity="HIGH", source_sensor="mq2_analog",
                observed_value=950.0, threshold_value=600.0, measurement_unit="adc_delta",
                reason="Combustible gas above safe level"),
    "FLOOD": dict(water_level=62.0, water_level_raw_adc=3300, hazard_severity="HIGH", source_sensor="water_level",
                  observed_value=62.0, threshold_value=30.0, measurement_unit="cm",
                  reason="Water level above safe limit"),
}


class DemoAlert(BaseModel):
    event_type: Literal["ACCIDENT", "FIRE", "GAS", "FLOOD"]


@router.get("/iot/devices")
def list_devices(user: User = Depends(require_roles(*CONTROL_ROOM_ROLES)), db: Session = Depends(get_db)):
    """Registered hardware units with their latest reading (for the sensor-network panel)."""
    out = []
    for d in db.query(Device).order_by(Device.device_id).all():
        last = (db.query(SensorReading).filter_by(device_id=d.device_id)
                .order_by(SensorReading.timestamp.desc()).first())
        alerts = db.query(SensorReading).filter_by(device_id=d.device_id, alert_qualified=True).count()
        out.append({
            "device_id": d.device_id, "name": d.name, "location_label": d.location_label,
            "latitude": d.latitude, "longitude": d.longitude, "active": d.active,
            "last_seen_at": d.last_seen_at, "firmware_version": d.firmware_version, "alerts_total": alerts,
            "transport": d.last_transport or (last.transport if last else None),
            "signal_quality": d.last_signal_quality if d.last_signal_quality is not None else (last.signal_quality if last else None),
            "last_event": None if not last else {
                "event_type": last.event_type, "reason": last.reason, "observed_value": last.observed_value,
                "measurement_unit": last.measurement_unit, "threshold_value": last.threshold_value,
                "fsr_raw_adc": last.fsr_raw_adc, "timestamp": last.timestamp,
                "incident_id": last.incident_id, "alert_qualified": last.alert_qualified},
        })
    return out


@router.post("/iot/devices/{device_id}/demo-alert", response_model=IoTEventResponse)
def demo_alert(device_id: str, body: DemoAlert, background: BackgroundTasks, user: User = Depends(require_roles("ADMIN")),
               db: Session = Depends(get_db)):
    """Admin-only demo: injects a qualified alert for a registered unit through the SAME pipeline the
    ESP32 uses (ingest -> incident -> routing -> notifications). Disabled in production."""
    if settings.APP_ENV == "production":
        raise HTTPException(403, detail={"error": "DEMO_DISABLED"})
    if not db.get(Device, device_id):
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Unknown device."})
    r = _DEMO_READINGS[body.event_type]
    ev = IoTEventCreate(device_id=device_id, event_id=f"{device_id}:console:{uuid.uuid4().hex[:10]}",
                        event_type=body.event_type, alert_qualified=True, simulated=False,
                        transport="GPRS" if body.event_type == "ACCIDENT" else "WIFI",
                        firmware_version="console-demo", **r)  # tagged as demo via firmware_version + audit log
    AuditService.record(db, f"user:{user.id}", "iot.demo_alert", "device", device_id, {"event_type": body.event_type})
    ack = IoTService.ingest_sensor_event(db, ev)
    _prewarm(background, ack)
    return ack
