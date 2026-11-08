"""
Notification state machine. Honest states:
  CREATED -> PENDING (queued for dashboard) -> SENT (pushed to >=1 open control-room socket)
  -> DELIVERED (only when the receiving dashboard confirms receipt) -> ACKNOWLEDGED (operator action)
  PENDING/SENT/DELIVERED past ack_deadline -> ESCALATED (admin alerted). FAILED for provider errors.
Inserting a row is never reported as delivery.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.operations import Notification
from app.services.audit_service import AuditService
from app.services.realtime import manager


def _now():
    return datetime.now(timezone.utc)


def _push_history(n: Notification, status: str, detail: str = "") -> None:
    n.history = list(n.history or []) + [{"status": status, "at": _now().isoformat(), "detail": detail}]
    n.status = status


class NotificationService:
    @staticmethod
    def ensure_for_departments(db: Session, incident_id: str, departments: List[str], severity: str) -> List[Notification]:
        """Idempotent: one DASHBOARD notification per (incident, department)."""
        created = []
        minutes = settings.ACK_DEADLINE_CRITICAL_MIN if severity == "CRITICAL" else settings.ACK_DEADLINE_DEFAULT_MIN
        for dep in departments:
            existing = db.query(Notification).filter_by(incident_id=incident_id, department=dep, channel="DASHBOARD").first()
            if existing:
                if existing.status == "CANCELLED":
                    _push_history(existing, "PENDING", "re-included by updated routing decision")
                    existing.ack_deadline = _now() + timedelta(minutes=minutes)
                continue
            n = Notification(incident_id=incident_id, department=dep, channel="DASHBOARD", status="CREATED",
                             history=[], ack_deadline=_now() + timedelta(minutes=minutes))
            _push_history(n, "CREATED")
            _push_history(n, "PENDING", "queued for control-room dashboard")
            db.add(n)
            created.append(n)
        db.flush()
        return created

    @staticmethod
    def cancel_for_departments(db: Session, incident_id: str, departments: List[str], reason: str) -> None:
        for n in db.query(Notification).filter(Notification.incident_id == incident_id,
                                               Notification.department.in_(departments)).all():
            if n.status not in ("ACKNOWLEDGED", "CANCELLED"):
                _push_history(n, "CANCELLED", reason)

    @staticmethod
    def dispatch_pending(db: Session, incident_id: str, payload_builder) -> None:
        """Push PENDING notifications over WebSocket. Marks SENT only if a socket received it."""
        for n in db.query(Notification).filter_by(incident_id=incident_id, status="PENDING").all():
            n.attempts += 1
            sent = manager.publish(n.department, {"type": "incident.notification", "notification_id": n.id,
                                                  "incident": payload_builder(n.department)})
            if sent:
                _push_history(n, "SENT", f"pushed to {sent} open dashboard connection(s)")
        db.flush()

    @staticmethod
    def mark_delivered(db: Session, notification_id: str, department: str) -> Optional[Notification]:
        n = db.get(Notification, notification_id)
        if not n or n.department != department:
            return None
        if n.status in ("PENDING", "SENT", "ESCALATED"):
            _push_history(n, "DELIVERED", "receipt confirmed by dashboard client")
        return n

    @staticmethod
    def acknowledge(db: Session, incident_id: str, department: str, user_id: str, actor: str) -> Optional[Notification]:
        n = db.query(Notification).filter_by(incident_id=incident_id, department=department, channel="DASHBOARD").first()
        if not n:
            return None
        if n.status != "ACKNOWLEDGED":
            n.acknowledged_by = user_id
            n.acknowledged_at = _now()
            _push_history(n, "ACKNOWLEDGED", f"by {actor}")
            AuditService.record(db, actor, "notification.acknowledge", "incident", incident_id, {"department": department})
        return n

    @staticmethod
    def run_escalations(db: Session) -> int:
        now = _now()
        overdue = db.query(Notification).filter(Notification.status.in_(("PENDING", "SENT", "DELIVERED")),
                                                Notification.ack_deadline < now).all()
        for n in overdue:
            n.escalated_at = now
            _push_history(n, "ESCALATED", "acknowledgement deadline passed")
            AuditService.record(db, "system", "notification.escalate", "incident", n.incident_id, {"department": n.department})
            manager.publish("ADMIN", {"type": "notification.escalated", "incident_id": n.incident_id,
                                      "department": n.department, "notification_id": n.id})
        if overdue:
            db.commit()
        return len(overdue)

    @staticmethod
    def to_dict(n: Notification) -> dict:
        return {"id": n.id, "department": n.department, "channel": n.channel, "status": n.status,
                "attempts": n.attempts, "ack_deadline": n.ack_deadline, "acknowledged_at": n.acknowledged_at,
                "escalated_at": n.escalated_at, "history": n.history or []}
