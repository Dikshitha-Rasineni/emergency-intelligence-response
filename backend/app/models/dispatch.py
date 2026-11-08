"""Response units (ambulances, fire tenders, patrols, rescue teams) and their dispatches to incidents."""
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models._common import utcnow, new_uuid

UNIT_TYPES = ("AMBULANCE", "FIRE_TENDER", "RESCUE_TENDER", "POLICE_PATROL", "HIGHWAY_PATROL", "DISASTER_TEAM", "RESCUE_BOAT")
UNIT_DEPARTMENT = {"AMBULANCE": "HOSPITAL", "FIRE_TENDER": "FIRE", "RESCUE_TENDER": "FIRE", "POLICE_PATROL": "POLICE",
                   "HIGHWAY_PATROL": "POLICE", "DISASTER_TEAM": "DISASTER", "RESCUE_BOAT": "DISASTER"}
UNIT_STATUSES = ("AVAILABLE", "ASSIGNED", "EN_ROUTE", "ON_SCENE", "TRANSPORTING", "RETURNING", "OUT_OF_SERVICE")
DISPATCH_STATUSES = ("ASSIGNED", "EN_ROUTE", "ON_SCENE", "TRANSPORTING", "AT_HOSPITAL", "COMPLETED", "CANCELLED")
ACTIVE_DISPATCH = ("ASSIGNED", "EN_ROUTE", "ON_SCENE", "TRANSPORTING", "AT_HOSPITAL")


class ResponseUnit(Base):
    __tablename__ = "response_units"

    id = Column(String(30), primary_key=True)
    call_sign = Column(String(80), nullable=False)
    unit_type = Column(String(30), nullable=False)
    department = Column(String(20), nullable=False, index=True)
    base_resource_id = Column(String(50), ForeignKey("emergency_resources.id", ondelete="SET NULL"), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    position_source = Column(String(20), default="STATION", nullable=False)  # STATION | CREW_GPS
    position_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="AVAILABLE", nullable=False, index=True)
    capabilities = Column(JSON, default=list, nullable=False)
    crew_token_hash = Column(String(128), nullable=True)
    data_source = Column(String(30), default="DEMO_SEED", nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    dispatches = relationship("Dispatch", back_populates="unit")


class Dispatch(Base):
    __tablename__ = "dispatches"

    id = Column(String(36), primary_key=True, default=new_uuid)
    incident_id = Column(String(50), ForeignKey("emergency_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_id = Column(String(30), ForeignKey("response_units.id", ondelete="CASCADE"), nullable=False, index=True)
    department = Column(String(20), nullable=False, index=True)
    status = Column(String(20), default="ASSIGNED", nullable=False, index=True)
    auto = Column(Boolean, default=False, nullable=False)
    assigned_by = Column(String(150), nullable=True)
    origin_lat = Column(Float, nullable=True)
    origin_lng = Column(Float, nullable=True)
    distance_km = Column(Float, nullable=True)
    eta_min = Column(Float, nullable=True)
    eta_source = Column(String(40), nullable=True)  # ROAD_ROUTE | STRAIGHT_LINE_ESTIMATE
    route = Column(JSON, nullable=True)  # [[lat, lng], ...]
    destination_resource_id = Column(String(50), ForeignKey("emergency_resources.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    en_route_at = Column(DateTime(timezone=True), nullable=True)
    on_scene_at = Column(DateTime(timezone=True), nullable=True)
    transporting_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    history = Column(JSON, default=list, nullable=False)

    incident = relationship("EmergencyReport", back_populates="dispatches")
    unit = relationship("ResponseUnit", back_populates="dispatches")
