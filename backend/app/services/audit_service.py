from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.operations import AuditEvent


class AuditService:
    @staticmethod
    def record(db: Session, actor: str, action: str, target_type: Optional[str] = None,
               target_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None,
               ip: Optional[str] = None) -> None:
        """Adds an audit row to the current transaction. Never put citizen free text or images in details."""
        db.add(AuditEvent(actor=actor, action=action, target_type=target_type, target_id=target_id,
                          details=details or {}, ip=ip))
