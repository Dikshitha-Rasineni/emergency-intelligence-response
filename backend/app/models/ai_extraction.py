from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models._common import utcnow, new_uuid


class AIExtraction(Base):
    __tablename__ = "ai_extractions"

    id = Column(String(36), primary_key=True, default=new_uuid)
    incident_id = Column(String(50), ForeignKey("emergency_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    emergency_type = Column(String(100), nullable=False)
    category = Column(String(40), nullable=True)
    affected_people = Column(Integer, default=0, nullable=False)
    injuries = Column(Integer, default=0, nullable=False)
    critical_indicators = Column(JSON, default=list, nullable=False)
    hazards = Column(JSON, default=list, nullable=False)
    needs = Column(JSON, default=list, nullable=False)  # medical, rescue, security, traffic, evacuation
    uncertainties = Column(JSON, default=list, nullable=False)
    location_information = Column(Text, nullable=True)
    english_summary = Column(Text, nullable=True)
    method = Column(String(30), default="rule_based", nullable=False)  # llm | rule_based
    model_name = Column(String(100), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    validation_notes = Column(JSON, default=list, nullable=False)
    raw_response = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    incident = relationship("EmergencyReport", back_populates="ai_extractions")
