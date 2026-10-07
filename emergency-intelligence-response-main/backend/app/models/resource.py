import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class EmergencyResource(Base):
    __tablename__ = "emergency_resources"

    id = Column(String(50), primary_key=True)  # e.g. "RES-H1", "HOSP-01" or UUID
    name = Column(String(150), nullable=False)
    resource_type = Column(String(50), nullable=False, index=True)  # HOSPITAL, AMBULANCE, POLICE, FIRE
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    capabilities = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    availability = relationship("ResourceAvailability", back_populates="resource", uselist=False, cascade="all, delete-orphan")
    incident_associations = relationship("IncidentResource", back_populates="resource", cascade="all, delete-orphan")


class ResourceAvailability(Base):
    __tablename__ = "resource_availability"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_id = Column(String(50), ForeignKey("emergency_resources.id", ondelete="CASCADE"), unique=True, nullable=False)
    available_units = Column(Integer, default=1, nullable=False)
    wait_time = Column(Integer, default=0, nullable=False)  # in minutes
    status = Column(String(50), default="AVAILABLE", nullable=False)  # AVAILABLE, BUSY, OFFLINE
    operational_details = Column(JSON, default=dict, nullable=False)  # beds, tenders, patrol units, etc.
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    resource = relationship("EmergencyResource", back_populates="availability")


class IncidentResource(Base):
    __tablename__ = "incident_resources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(50), ForeignKey("emergency_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_id = Column(String(50), ForeignKey("emergency_resources.id", ondelete="CASCADE"), nullable=False, index=True)
    distance = Column(Float, nullable=False)  # km
    suitability_score = Column(Float, nullable=False)  # 0 to 100
    ranking = Column(Integer, default=1, nullable=False)
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    incident = relationship("EmergencyReport", back_populates="incident_resources")
    resource = relationship("EmergencyResource", back_populates="incident_associations")
