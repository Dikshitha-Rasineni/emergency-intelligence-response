from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models._common import utcnow, new_uuid


class EmergencyResource(Base):
    __tablename__ = "emergency_resources"

    id = Column(String(50), primary_key=True)
    name = Column(String(150), nullable=False)
    resource_type = Column(String(50), nullable=False, index=True)  # HOSPITAL, AMBULANCE, POLICE, FIRE, SHELTER, DISASTER
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    capabilities = Column(JSON, default=list, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    data_source = Column(String(50), default="ADMIN", nullable=False)  # ADMIN, DEMO_SEED, OSM
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    # PostGIS: a `geom geography(Point,4326)` column is maintained by a DB trigger (see migration c3e9...).

    availability = relationship("ResourceAvailability", back_populates="resource", uselist=False, cascade="all, delete-orphan")
    incident_associations = relationship("IncidentResource", back_populates="resource", cascade="all, delete-orphan")


class ResourceAvailability(Base):
    __tablename__ = "resource_availability"

    id = Column(String(36), primary_key=True, default=new_uuid)
    resource_id = Column(String(50), ForeignKey("emergency_resources.id", ondelete="CASCADE"), unique=True, nullable=False)
    available_units = Column(Integer, default=0, nullable=False)
    wait_time = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="UNKNOWN", nullable=False)  # AVAILABLE, BUSY, OFFLINE, UNKNOWN
    verified = Column(Boolean, default=False, nullable=False)  # true only when an authorized org user reported it
    reported_by = Column(String(36), nullable=True)
    operational_details = Column(JSON, default=dict, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    resource = relationship("EmergencyResource", back_populates="availability")


class IncidentResource(Base):
    __tablename__ = "incident_resources"

    id = Column(String(36), primary_key=True, default=new_uuid)
    incident_id = Column(String(50), ForeignKey("emergency_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_id = Column(String(50), ForeignKey("emergency_resources.id", ondelete="CASCADE"), nullable=False, index=True)
    distance = Column(Float, nullable=False)  # straight-line km (PostGIS); road distance comes from routing
    suitability_score = Column(Float, nullable=False)
    ranking = Column(Integer, default=1, nullable=False)
    assigned_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    incident = relationship("EmergencyReport", back_populates="incident_resources")
    resource = relationship("EmergencyResource", back_populates="incident_associations")
