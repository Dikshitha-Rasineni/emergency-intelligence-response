from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models._common import utcnow, new_uuid

MEDIA_STATUSES = ("UPLOAD_RECEIVED", "PROCESSING", "ANALYSIS_COMPLETED", "REVIEW_REQUIRED", "PROCESSING_FAILED", "NOT_ANALYZED")


class IncidentMedia(Base):
    __tablename__ = "incident_media"

    id = Column(String(36), primary_key=True, default=new_uuid)
    incident_id = Column(String(50), ForeignKey("emergency_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String(10), nullable=False, default="image")  # image | audio
    storage_key = Column(String(255), nullable=False)  # path relative to UPLOAD_DIR; never served publicly
    mime_type = Column(String(50), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    exif_stripped = Column(Boolean, default=True, nullable=False)
    exif_gps_present = Column(Boolean, default=False, nullable=False)  # recorded, never trusted as location
    duplicate_of = Column(String(36), nullable=True)
    status = Column(String(30), default="UPLOAD_RECEIVED", nullable=False)
    analysis = Column(JSON, nullable=True)
    analysis_error = Column(Text, nullable=True)
    model_name = Column(String(100), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    analyzed_at = Column(DateTime(timezone=True), nullable=True)
    purge_after = Column(DateTime(timezone=True), nullable=True)

    incident = relationship("EmergencyReport", back_populates="media")
