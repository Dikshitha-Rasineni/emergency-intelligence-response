"""Authorized control-room endpoints. Every response is English-only and filtered per department."""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_roles, CONTROL_ROOM_ROLES
from app.core.security import decode_access_token
from app.db.session import get_db, SessionLocal
from app.models.incident import EmergencyReport
from app.models.operations import IncidentUpdate, Notification, RoutingDecision
from app.models.user import User
from app.schemas.incident import StatusUpdate, PriorityOverride, Page
from app.services.audit_service import AuditService
from app.services.incident_service import IncidentService, OPEN_STATUSES
from app.services.notification_service import NotificationService
from app.services.realtime import manager
from app.services.response_copilot_service import ResponseCopilot
from app.services.genai_service import GenAIService
from pydantic import BaseModel, Field

router = APIRouter()
any_control_room = require_roles(*CONTROL_ROOM_ROLES)


def _dept(user: User, as_department: Optional[str]) -> str:
    role = user.role.upper()
    if role == "ADMIN" and as_department:
        d = as_department.upper()
        if d not in ("HOSPITAL", "POLICE", "FIRE", "DISASTER", "ADMIN"):
            raise HTTPException(400, detail={"error": "BAD_DEPARTMENT"})
        return d
    return role


def _load(db: Session, incident_id: str, dept: str) -> EmergencyReport:
    inc = db.get(EmergencyReport, incident_id)
    if inc and inc.merged_into_id:  # follow duplicate-merge links to the canonical incident
        inc = db.get(EmergencyReport, inc.merged_into_id)
    if not inc:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Incident not found."})
    if not IncidentService.is_routed_to(inc, dept):
        # Same response as not found: do not reveal incidents routed elsewhere.
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "This incident is not in your service's queue. "
                                         "It was routed only to the services it needs, or the ID is wrong."})
    return inc


def _row(db: Session, inc: EmergencyReport, dept: str) -> dict:
    v = IncidentService.department_view(db, inc, dept)
    keep = ("incident_id", "category", "emergency_type", "priority_score", "severity", "status", "source",
            "created_at", "location", "english_summary", "injuries", "affected_people", "trapped", "routing",
            "notification", "linked_report_count", "evidence_sources", "department_view")
    return {k: v.get(k) for k in keep if k in v}


@router.get("/control-room/incidents", response_model=Page)
def list_incidents(status: Optional[str] = Query("open"), limit: int = Query(25, ge=1, le=100),
                   offset: int = Query(0, ge=0), as_department: Optional[str] = None,
                   user: User = Depends(any_control_room), db: Session = Depends(get_db)):
    dept = _dept(user, as_department)
    NotificationService.run_escalations(db)
    total, rows = IncidentService.list_for_department(db, dept, status, limit, offset)
    items = [_row(db, r, dept) for r in rows]
    items.sort(key=lambda x: (x.get("status") not in OPEN_STATUSES, -(x.get("priority_score") or 0)))
    return Page(total=total, limit=limit, offset=offset, items=items)


@router.get("/control-room/summary")
def summary(as_department: Optional[str] = None, user: User = Depends(any_control_room), db: Session = Depends(get_db)):
    dept = _dept(user, as_department)
    q = db.query(Notification.status, func.count()).filter(Notification.department == dept) if dept != "ADMIN" \
        else db.query(Notification.status, func.count())
    by_status = {s: c for s, c in q.group_by(Notification.status).all()}
    total_open, rows = IncidentService.list_for_department(db, dept, "open", 500, 0)
    sev = {}
    for r in rows:
        a = r.severity_assessments[0] if r.severity_assessments else None
        if a:
            sev[a.severity] = sev.get(a.severity, 0) + 1
    return {"department": dept, "open_incidents": total_open, "by_severity": sev, "notifications": by_status,
            "live_connections": manager.connected_count(dept)}


@router.get("/control-room/incidents/{incident_id}")
def get_incident(incident_id: str, as_department: Optional[str] = None, route: bool = True,
                 user: User = Depends(any_control_room), db: Session = Depends(get_db)):
    dept = _dept(user, as_department)
    inc = _load(db, incident_id, dept)
    if dept == "ADMIN":
        view = IncidentService.full_view(db, inc)
        view["department_view"] = "ADMIN"
    else:
        view = IncidentService.department_view(db, inc, dept, with_route=route)
        view["brief"] = ResponseCopilot.brief(view)
    view["genai_brief"] = GenAIService.cached_brief(inc, view, dept)  # instant if already generated
    AuditService.record(db, user.email, "incident.view", "incident", inc.id, {"department": dept})
    db.commit()
    return view


@router.get("/control-room/incidents/{incident_id}/genai-brief")
def genai_brief(incident_id: str, refresh: bool = False, as_department: Optional[str] = None,
                user: User = Depends(any_control_room), db: Session = Depends(get_db)):
    """GenAI incident brief for this control room: generated from the verified record + retrieved guidance,
    grounding-checked, cached until the facts change."""
    dept = _dept(user, as_department)
    inc = _load(db, incident_id, dept)
    view = IncidentService.full_view(db, inc) if dept == "ADMIN" else IncidentService.department_view(db, inc, dept, with_route=False)
    out = GenAIService.brief(db, inc, view, dept, force=refresh)
    AuditService.record(db, user.email, "genai.brief", "incident", inc.id, {"department": dept, "grounding": out.get("grounding")})
    db.commit()
    return out


class AskBody(BaseModel):
    question: str = Field(..., min_length=2, max_length=400)


@router.post("/control-room/incidents/{incident_id}/ask")
def ask_resq(incident_id: str, body: AskBody, as_department: Optional[str] = None,
             user: User = Depends(any_control_room), db: Session = Depends(get_db)):
    """Ask RESQ: a question about one incident, answered by GenAI from the record and guidance only."""
    dept = _dept(user, as_department)
    inc = _load(db, incident_id, dept)
    view = IncidentService.full_view(db, inc) if dept == "ADMIN" else IncidentService.department_view(db, inc, dept, with_route=False)
    out = GenAIService.ask(db, view, dept, body.question)
    AuditService.record(db, user.email, "genai.ask", "incident", inc.id, {"department": dept, "question": body.question[:200],
                                                                          "grounded": out.get("grounded")})
    db.commit()
    return out


@router.post("/control-room/incidents/{incident_id}/acknowledge")
def acknowledge(incident_id: str, user: User = Depends(require_roles("HOSPITAL", "POLICE", "FIRE", "DISASTER")),
                db: Session = Depends(get_db)):
    dept = user.role.upper()
    inc = _load(db, incident_id, dept)
    n = NotificationService.acknowledge(db, inc.id, dept, user.id, user.email)
    if not n:
        raise HTTPException(409, detail={"error": "NO_NOTIFICATION", "message": "No notification for this department."})
    if inc.status == "REPORTED":
        inc.status = "ACKNOWLEDGED"
    db.add(IncidentUpdate(incident_id=inc.id, actor_user_id=user.id, actor_label=f"{dept} control room",
                          department=dept, status="ACKNOWLEDGED", public=True, note=None))
    db.commit()
    manager.publish(dept, {"type": "incident.updated", "incident_id": inc.id})
    return NotificationService.to_dict(n)


@router.post("/control-room/incidents/{incident_id}/status")
def update_status(incident_id: str, body: StatusUpdate, background: BackgroundTasks,
                  user: User = Depends(require_roles("HOSPITAL", "POLICE", "FIRE", "DISASTER", "ADMIN")),
                  db: Session = Depends(get_db)):
    dept = user.role.upper()
    inc = _load(db, incident_id, dept)
    old = inc.status
    inc.status = body.status
    upd = IncidentUpdate(incident_id=inc.id, actor_user_id=user.id, actor_label=f"{dept} control room",
                         department=dept, status=body.status, note=body.note, public=body.public)
    db.add(upd)
    db.flush()
    if body.public and body.note:
        background.add_task(IncidentService.translate_public_note, upd.id)
    AuditService.record(db, user.email, "incident.status", "incident", inc.id, {"from": old, "to": body.status})
    if body.status in ("RESOLVED", "CLOSED", "FALSE_ALARM"):
        for n in inc.notifications:
            if n.status not in ("ACKNOWLEDGED", "CANCELLED"):
                n.history = list(n.history or []) + [{"status": "CANCELLED", "at": str(inc.updated_at), "detail": f"incident {body.status}"}]
                n.status = "CANCELLED"
    db.commit()
    for d in inc.routing_decisions:
        if d.included and not d.superseded:
            manager.publish(d.department, {"type": "incident.updated", "incident_id": inc.id})
    return {"incident_id": inc.id, "status": inc.status}


@router.post("/control-room/incidents/{incident_id}/priority-override")
def override_priority(incident_id: str, body: PriorityOverride,
                      user: User = Depends(require_roles("HOSPITAL", "POLICE", "FIRE", "DISASTER", "ADMIN")),
                      db: Session = Depends(get_db)):
    """Authorized assessment override. Recorded as a new assessment with the user and reason."""
    dept = user.role.upper()
    inc = _load(db, incident_id, dept)
    prev = inc.severity_assessments[0] if inc.severity_assessments else None
    result = IncidentService.assess(db, inc, override={"score": body.score, "reason": body.reason, "user_id": user.id})
    AuditService.record(db, user.email, "incident.priority_override", "incident", inc.id,
                        {"from": prev.priority_score if prev else None, "to": body.score, "reason": body.reason})
    db.commit()
    IncidentService.push_updates(db, inc)
    return {"incident_id": inc.id, "priority_score": result["score"], "severity": result["severity"]}


@router.post("/control-room/notifications/{notification_id}/delivered")
def confirm_delivery(notification_id: str, user: User = Depends(require_roles("HOSPITAL", "POLICE", "FIRE", "DISASTER")),
                     db: Session = Depends(get_db)):
    n = NotificationService.mark_delivered(db, notification_id, user.role.upper())
    if not n:
        raise HTTPException(404, detail={"error": "NOT_FOUND"})
    db.commit()
    return NotificationService.to_dict(n)


@router.websocket("/ws/control-room")
async def control_room_socket(ws: WebSocket, token: str = Query(...)):
    payload = decode_access_token(token)
    if not payload:
        await ws.close(code=4401)
        return
    db = SessionLocal()
    try:
        user = db.get(User, payload.get("sub"))
        if not user or not user.is_active or user.role.upper() not in CONTROL_ROOM_ROLES:
            await ws.close(code=4403)
            return
        dept = user.role.upper()
    finally:
        db.close()
    await manager.connect(ws, dept)
    try:
        await ws.send_json({"type": "hello", "department": dept})
        while True:
            msg = await ws.receive_json()
            if msg.get("type") == "delivered" and msg.get("notification_id") and dept != "ADMIN":
                s = SessionLocal()
                try:
                    if NotificationService.mark_delivered(s, msg["notification_id"], dept):
                        s.commit()
                finally:
                    s.close()
    except (WebSocketDisconnect, RuntimeError, ValueError):
        pass
    finally:
        manager.disconnect(ws)
