"""Unit dispatch endpoints: control rooms assign units; crews update status and share GPS."""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.dispatch import ResponseUnit, Dispatch, ACTIVE_DISPATCH
from app.models.incident import EmergencyReport
from app.models.resource import EmergencyResource
from app.models.user import User
from app.services.audit_service import AuditService
from app.services.dispatch_service import DispatchService, UNIT_LABEL, _now
from app.services.incident_service import IncidentService

router = APIRouter()
services = require_roles("HOSPITAL", "POLICE", "FIRE", "DISASTER", "ADMIN")


class DispatchBody(BaseModel):
    unit_id: str = Field(..., max_length=30)


class StatusBody(BaseModel):
    status: str = Field(..., pattern="^(EN_ROUTE|ON_SCENE|TRANSPORTING|AT_HOSPITAL|COMPLETED|CANCELLED)$")


class LocationBody(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy_m: Optional[float] = Field(None, ge=0, le=10000)


def _dept(user: User, as_department: Optional[str]) -> str:
    role = user.role.upper()
    if role == "ADMIN":
        if not as_department:
            raise HTTPException(400, detail={"error": "DEPARTMENT_REQUIRED", "message": "Choose a department."})
        return as_department.upper()
    return role


def _incident(db: Session, incident_id: str, dept: str) -> EmergencyReport:
    inc = db.get(EmergencyReport, incident_id)
    if inc and inc.merged_into_id:
        inc = db.get(EmergencyReport, inc.merged_into_id)
    if not inc or not IncidentService.is_routed_to(inc, dept):
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "This incident is not in your service's queue."})
    return inc


def _push(db: Session, inc: EmergencyReport):
    db.refresh(inc)
    IncidentService.push_updates(db, inc)


# ---------------------------------------------------------------- control room
@router.get("/control-room/incidents/{incident_id}/units")
def unit_candidates(incident_id: str, as_department: Optional[str] = None, user: User = Depends(services),
                    db: Session = Depends(get_db)):
    """Nearest available units of your department with distance and ETA."""
    dept = _dept(user, as_department)
    inc = _incident(db, incident_id, dept)
    return DispatchService.candidates(db, inc, dept)


@router.post("/control-room/incidents/{incident_id}/dispatch")
def dispatch_unit(incident_id: str, body: DispatchBody, user: User = Depends(services), db: Session = Depends(get_db)):
    unit = db.get(ResponseUnit, body.unit_id)
    if not unit or not unit.active:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Unit not found."})
    dept = unit.department if user.role.upper() == "ADMIN" else user.role.upper()
    if unit.department != dept:
        raise HTTPException(403, detail={"error": "FORBIDDEN", "message": "You can only dispatch your own service's units."})
    inc = _incident(db, incident_id, dept)
    if unit.status != "AVAILABLE":
        raise HTTPException(409, detail={"error": "UNIT_BUSY", "message": f"{unit.call_sign} is {unit.status.lower()}."})
    d = DispatchService.dispatch(db, inc, unit, f"{dept} control room ({user.email})")
    AuditService.record(db, user.email, "unit.dispatch", "incident", inc.id, {"unit": unit.id})
    db.commit()
    _push(db, inc)
    return DispatchService.control_dict(db, d)


@router.post("/control-room/dispatches/{dispatch_id}/status")
def dispatch_status(dispatch_id: str, body: StatusBody, user: User = Depends(services), db: Session = Depends(get_db)):
    d = db.get(Dispatch, dispatch_id)
    if not d or (user.role.upper() != "ADMIN" and d.department != user.role.upper()):
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Dispatch not found."})
    try:
        DispatchService.set_status(db, d, body.status, f"{d.department} control room ({user.email})")
    except ValueError as e:
        raise HTTPException(409, detail={"error": "BAD_TRANSITION", "message": str(e)})
    AuditService.record(db, user.email, "unit.status", "dispatch", d.id, {"status": body.status})
    db.commit()
    _push(db, d.incident)
    return DispatchService.control_dict(db, d)


@router.post("/control-room/units/{unit_id}/crew-link")
def crew_link(unit_id: str, user: User = Depends(services), db: Session = Depends(get_db)):
    """Creates a new private link for the crew's phone (the previous link stops working)."""
    unit = db.get(ResponseUnit, unit_id)
    if not unit or (user.role.upper() != "ADMIN" and unit.department != user.role.upper()):
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Unit not found."})
    token = DispatchService.new_crew_token(unit)
    AuditService.record(db, user.email, "unit.crew_link", "unit", unit.id, {})
    db.commit()
    return {"unit_id": unit.id, "path": f"/crew/{unit.id}?t={token}"}


@router.get("/control-room/units")
def list_units(as_department: Optional[str] = None, user: User = Depends(services), db: Session = Depends(get_db)):
    """Fleet board: every unit of your service (admin: all, or one department)."""
    q = db.query(ResponseUnit).filter(ResponseUnit.active.is_(True))
    dept = user.role.upper() if user.role.upper() != "ADMIN" else (as_department or "").upper()
    if dept:
        q = q.filter(ResponseUnit.department == dept)
    out = []
    for u in q.order_by(ResponseUnit.department, ResponseUnit.id).all():
        cur = DispatchService.current_for_unit(db, u)
        out.append({**DispatchService.unit_dict(u),
                    "dispatch": ({"id": cur.id, "incident_id": cur.incident_id, "status": cur.status,
                                  **DispatchService.live(cur)} if cur else None)})
    return out


# ---------------------------------------------------------------- crew phone
def _crew(db: Session, unit_id: str, token: Optional[str]) -> ResponseUnit:
    u = DispatchService.crew_unit(db, unit_id, token)
    if not u:
        raise HTTPException(401, detail={"error": "INVALID_CREW_LINK", "message": "This crew link is not valid any more. Ask your control room for a new one."})
    return u


@router.get("/crew/{unit_id}")
def crew_view(unit_id: str, x_crew_token: Optional[str] = Header(None), db: Session = Depends(get_db)):
    unit = _crew(db, unit_id, x_crew_token)
    d = DispatchService.current_for_unit(db, unit)
    if d:
        DispatchService.tick(db, d)
        db.commit()
    job = None
    if d:
        inc = d.incident
        full = IncidentService.full_view(db, inc)
        dest = db.get(EmergencyResource, d.destination_resource_id) if d.destination_resource_id else None
        job = {"dispatch": DispatchService.control_dict(db, d),
               "incident": {"id": inc.id, "type": full.get("emergency_type"), "category": full.get("category"),
                            "severity": full.get("severity"), "priority_score": full.get("priority_score"),
                            "summary": full.get("english_summary"), "location": full.get("location"),
                            "injuries": full.get("injuries"), "trapped": full.get("trapped"),
                            "hazards": full.get("hazards"), "sensor": (full.get("sensor_evidence") or [None])[0],
                            "other_units": [x for x in full.get("dispatches", []) if x["id"] != d.id]},
               "destination": {"name": dest.name, "latitude": dest.latitude, "longitude": dest.longitude} if dest else None}
    return {"unit": DispatchService.unit_dict(unit), "unit_label": UNIT_LABEL.get(unit.unit_type), "job": job}


@router.post("/crew/{unit_id}/status")
def crew_status(unit_id: str, body: StatusBody, x_crew_token: Optional[str] = Header(None), db: Session = Depends(get_db)):
    unit = _crew(db, unit_id, x_crew_token)
    d = DispatchService.current_for_unit(db, unit)
    if not d:
        raise HTTPException(409, detail={"error": "NO_ASSIGNMENT", "message": "No active assignment."})
    try:
        DispatchService.set_status(db, d, body.status, f"crew {unit.call_sign}")
    except ValueError as e:
        raise HTTPException(409, detail={"error": "BAD_TRANSITION", "message": str(e)})
    db.commit()
    _push(db, d.incident)
    return {"status": d.status}


@router.post("/crew/{unit_id}/location")
def crew_location(unit_id: str, body: LocationBody, x_crew_token: Optional[str] = Header(None), db: Session = Depends(get_db)):
    unit = _crew(db, unit_id, x_crew_token)
    unit.latitude, unit.longitude = body.latitude, body.longitude
    unit.position_source, unit.position_at = "CREW_GPS", _now()
    db.commit()
    d = DispatchService.current_for_unit(db, unit)
    if d:
        _push(db, d.incident)
    return {"ok": True}
