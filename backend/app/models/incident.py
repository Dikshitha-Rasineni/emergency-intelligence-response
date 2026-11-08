from sqlalchemy import Column, String, Float, Integer, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models._common import utcnow

# Status lifecycle (control-room actions move it forward; every change is in incident_updates)
INCIDENT_STATUSES = ("MERGED", "REPORTED", "ACKNOWLEDGED", "RESPONDING", "ON_SCENE", "RESOLVED", "CLOSED", "FALSE_ALARM")


class EmergencyReport(Base):
    """Canonical incident record. Citizen reports and IoT events both converge here."""
    __tablename__ = "emergency_reports"

    id = Column(String(50), primary_key=True)
    description = Column(Text, nullable=False)  # original text exactly as submitted
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)
    location = Column(String(255), nullable=True)
    location_source = Column(String(50), default="UNVERIFIED", nullable=True)
    coordinates_verified = Column(Boolean, default=False, nullable=True)
    location_accuracy_m = Column(Float, nullable=True)
    detected_language = Column(String(20), default="en", nullable=True)
    language_confidence = Column(Float, nullable=True)
    preferred_language = Column(String(20), nullable=True)
    # Machine translation of the original text into English for control rooms (null for English reports)
    english_translation = Column(Text, nullable=True)
    translation_provider = Column(String(60), nullable=True)
    # GenAI outputs cached per audience: {"brief:HOSPITAL": {...}, "citizen:te": {...}} with a facts signature
    genai = Column(JSON, nullable=True)
    category = Column(String(40), nullable=True, index=True)  # canonical code, e.g. road_accident
    user_selected_category = Column(String(40), nullable=True)
    affected_people = Column(Integer, default=0, nullable=False)
    injuries = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="REPORTED", nullable=False, index=True)
    source = Column(String(50), default="USER", nullable=False)  # USER, IOT, RESPONDER
    ai_status = Column(String(30), default="PENDING", nullable=False)  # PENDING, COMPLETED, RULE_BASED, UNAVAILABLE
    tracking_token_hash = Column(String(128), nullable=True)
    # Set when this report was merged into an existing open incident (duplicate of the same event)
    merged_into_id = Column(String(50), ForeignKey("emergency_reports.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    ai_extractions = relationship("AIExtraction", back_populates="incident", cascade="all, delete-orphan",
                                  order_by="AIExtraction.created_at.desc()")
    severity_assessments = relationship("SeverityAssessment", back_populates="incident", cascade="all, delete-orphan",
                                        order_by="SeverityAssessment.created_at.desc()")
    incident_resources = relationship("IncidentResource", back_populates="incident", cascade="all, delete-orphan")
    sensor_readings = relationship("SensorReading", back_populates="incident")
    recommendations = relationship("ResponseRecommendation", back_populates="incident", cascade="all, delete-orphan")
    media = relationship("IncidentMedia", back_populates="incident", cascade="all, delete-orphan",
                         order_by="IncidentMedia.created_at")
    routing_decisions = relationship("RoutingDecision", back_populates="incident", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="incident", cascade="all, delete-orphan")
    updates = relationship("IncidentUpdate", back_populates="incident", cascade="all, delete-orphan",
                           order_by="IncidentUpdate.created_at")
    dispatches = relationship("Dispatch", back_populates="incident", cascade="all, delete-orphan",
                              order_by="Dispatch.assigned_at")
