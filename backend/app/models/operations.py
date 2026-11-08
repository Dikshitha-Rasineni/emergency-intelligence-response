"""Department routing decisions, notifications, response history and audit log."""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models._common import utcnow, new_uuid

DEPARTMENTS = ("HOSPITAL", "POLICE", "FIRE", "DISASTER")
NOTIFICATION_STATUSES = ("CREATED", "PENDING", "SENT", "DELIVERED", "ACKNOWLEDGED", "FAILED", "ESCALATED", "CANCELLED")


class RoutingDecision(Base):
    __tablename__ = "routing_decisions"

    id = Column(String(36), primary_key=True, default=new_uuid)
    incident_id = Column(String(50), ForeignKey("emergency_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    department = Column(String(20), nullable=False)
    included = Column(Boolean, nullable=False)
    role_in_response = Column(String(20), nullable=True)  # PRIMARY | SUPPORTING | ESCALATION
    reasons = Column(JSON, default=list, nullable=False)
    policy_version = Column(String(30), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    superseded = Column(Boolean, default=False, nullable=False)

    incident = relationship("EmergencyReport", back_populates="routing_decisions")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (UniqueConstraint("incident_id", "department", "channel", name="uq_notification_incident_dept_channel"),)

    id = Column(String(36), primary_key=True, default=new_uuid)
    incident_id = Column(String(50), ForeignKey("emergency_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    department = Column(String(20), nullable=False, index=True)
    channel = Column(String(20), nullable=False, default="DASHBOARD")  # DASHBOARD | SMS | PUSH
    status = Column(String(20), nullable=False, default="CREATED", index=True)
    attempts = Column(Integer, default=0, nullable=False)
    ack_deadline = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(36), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    history = Column(JSON, default=list, nullable=False)  # [{status, at, detail}]
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    incident = relationship("EmergencyReport", back_populates="notifications")


class IncidentUpdate(Base):
    __tablename__ = "incident_updates"

    id = Column(String(36), primary_key=True, default=new_uuid)
    incident_id = Column(String(50), ForeignKey("emergency_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id = Column(String(36), nullable=True)
    actor_label = Column(String(150), nullable=True)
    department = Column(String(20), nullable=True)
    status = Column(String(30), nullable=True)
    note = Column(Text, nullable=True)
    public = Column(Boolean, default=False, nullable=False)  # visible to the citizen tracker
    note_translated = Column(Text, nullable=True)   # public note in the citizen's language
    note_language = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    incident = relationship("EmergencyReport", back_populates="updates")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=new_uuid)
    actor = Column(String(150), nullable=False)  # user id/email, "system", "device:<id>", "citizen"
    action = Column(String(80), nullable=False, index=True)
    target_type = Column(String(40), nullable=True)
    target_id = Column(String(100), nullable=True, index=True)
    details = Column(JSON, default=dict, nullable=False)
    ip = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(String(36), primary_key=True, default=new_uuid)
    title = Column(String(255), nullable=False)
    publisher = Column(String(255), nullable=False)
    source_url = Column(String(500), nullable=True)
    version = Column(String(50), nullable=True)
    published_on = Column(String(30), nullable=True)
    language = Column(String(10), default="en", nullable=False)
    categories = Column(JSON, default=list, nullable=False)  # applicability: fire, flood, road_accident ...
    approved = Column(Boolean, default=False, nullable=False)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(String(36), primary_key=True, default=new_uuid)
    document_id = Column(String(36), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    idx = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    # A `tsv tsvector` generated column + GIN index is created in the migration (PostgreSQL full-text search).

    document = relationship("KnowledgeDocument", back_populates="chunks")
