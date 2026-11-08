from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models._common import utcnow, new_uuid


class ResponseRecommendation(Base):
    __tablename__ = "response_recommendations"

    id = Column(String(36), primary_key=True, default=new_uuid)
    incident_id = Column(String(50), ForeignKey("emergency_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="USER")  # USER (citizen guidance)
    language = Column(String(10), nullable=True)
    summary = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    precautions = Column(JSON, default=list, nullable=False)
    precaution_sources = Column(JSON, default=list, nullable=False)
    operational_checklist = Column(JSON, default=list, nullable=False)
    missing_information = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    incident = relationship("EmergencyReport", back_populates="recommendations")
