import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Text, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base


class EmergencyReport(Base):
    __tablename__ = "emergency_reports"

    id = Column(String(50), primary_key=True, default=lambda: f"INC-{uuid.uuid4().hex[:8].upper()}")
    description = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    location = Column(String(255), nullable=True)
    affected_people = Column(Integer, default=0, nullable=False)
    injuries = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="REPORTED", nullable=False)  # REPORTED, ACKNOWLEDGED, DISPATCHED, RESOLVED
    source = Column(String(50), default="USER", nullable=False)  # USER, IOT, RESPONDER
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    ai_extractions = relationship("AIExtraction", back_populates="incident", cascade="all, delete-orphan")
    severity_assessments = relationship("SeverityAssessment", back_populates="incident", cascade="all, delete-orphan")
    incident_resources = relationship("IncidentResource", back_populates="incident", cascade="all, delete-orphan")
    sensor_readings = relationship("SensorReading", back_populates="incident", cascade="all, delete-orphan")
    recommendations = relationship("ResponseRecommendation", back_populates="incident", cascade="all, delete-orphan")
