import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class ResponseRecommendation(Base):
    __tablename__ = "response_recommendations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(50), ForeignKey("emergency_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="ALL")  # USER, HOSPITAL, POLICE, FIRE, ALL
    summary = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    precautions = Column(JSON, default=list, nullable=False)
    operational_checklist = Column(JSON, default=list, nullable=False)
    missing_information = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    incident = relationship("EmergencyReport", back_populates="recommendations")
