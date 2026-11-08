from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models._common import utcnow, new_uuid


class SeverityAssessment(Base):
    __tablename__ = "severity_assessments"

    id = Column(String(36), primary_key=True, default=new_uuid)
    incident_id = Column(String(50), ForeignKey("emergency_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    severity = Column(String(50), nullable=False)  # LOW, MODERATE, HIGH, CRITICAL
    priority_score = Column(Float, nullable=False)
    factors = Column(JSON, default=list, nullable=False)       # human-readable lines (legacy)
    evidence = Column(JSON, default=list, nullable=False)      # [{factor, points, source, observed_at}]
    uncertainties = Column(JSON, default=list, nullable=False)
    assessment_version = Column(String(30), default="rules-v2", nullable=False)
    assessed_by = Column(String(100), default="system", nullable=False)  # system or user id for overrides
    override_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    incident = relationship("EmergencyReport", back_populates="severity_assessments")
