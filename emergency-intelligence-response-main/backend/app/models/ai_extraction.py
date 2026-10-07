import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class AIExtraction(Base):
    __tablename__ = "ai_extractions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(50), ForeignKey("emergency_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    emergency_type = Column(String(100), nullable=False)
    affected_people = Column(Integer, default=0, nullable=False)
    injuries = Column(Integer, default=0, nullable=False)
    critical_indicators = Column(JSON, default=list, nullable=False)
    location_information = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    incident = relationship("EmergencyReport", back_populates="ai_extractions")
