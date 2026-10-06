from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class EmergencyReport(Base):
    __tablename__ = "emergency_reports"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: f"INC-{uuid4().hex[:8].upper()}",
    )

    description: Mapped[str] = mapped_column(Text, nullable=False)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    affected_people: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    injuries: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="reported",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
class AIExtraction(Base):
    __tablename__ = "ai_extractions"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: f"EXT-{uuid4().hex[:8].upper()}",
    )

    incident_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    emergency_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    affected_people: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    injuries: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    critical_indicators: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    location_information: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    
class SeverityAssessment(Base):
    __tablename__ = "severity_assessments"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: f"SEV-{uuid4().hex[:8].upper()}",
    )

    incident_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    priority_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    factors: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
class EmergencyResource(Base):
    __tablename__ = "emergency_resources"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: f"RES-{uuid4().hex[:8].upper()}",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    address: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    contact_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
class ResourceAvailability(Base):
    __tablename__ = "resource_availability"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: f"AVL-{uuid4().hex[:8].upper()}",
    )

    resource_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    available_units: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="available",
        nullable=False,
    )

    wait_time_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
class IncidentResource(Base):
    __tablename__ = "incident_resources"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: f"IR-{uuid4().hex[:8].upper()}",
    )

    incident_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    resource_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    distance_km: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    suitability_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    assignment_status: Mapped[str] = mapped_column(
        String(50),
        default="recommended",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: f"SEN-{uuid4().hex[:8].upper()}",
    )

    device_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    incident_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    temperature: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    smoke_level: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    water_level: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    impact: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
class ResponseRecommendation(Base):
    __tablename__ = "response_recommendations"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: f"REC-{uuid4().hex[:8].upper()}",
    )

    incident_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recommendation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    missing_information: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )