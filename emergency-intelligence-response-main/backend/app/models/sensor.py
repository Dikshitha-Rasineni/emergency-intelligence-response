import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(50), ForeignKey("emergency_reports.id", ondelete="SET NULL"), nullable=True, index=True)
    device_id = Column(String(50), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, default="TELEMETRY")
    temperature = Column(Float, nullable=True)
    smoke_level = Column(Float, nullable=True)
    water_level = Column(Float, nullable=True)
    impact = Column(Float, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    incident = relationship("EmergencyReport", back_populates="sensor_readings")
