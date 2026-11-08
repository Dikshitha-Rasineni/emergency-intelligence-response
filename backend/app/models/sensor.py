from sqlalchemy import Column, String, Float, Integer, BigInteger, Boolean, DateTime, ForeignKey
from app.models._common import utcnow, new_uuid
from sqlalchemy.orm import relationship
from app.db.session import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(String(36), primary_key=True, default=new_uuid)
    # Device-generated unique event id (device_id:boot:seq). Server-side idempotency key.
    event_id = Column(String(100), unique=True, nullable=True, index=True)
    transport = Column(String(10), nullable=True)  # WIFI | GPRS
    incident_id = Column(String(50), ForeignKey("emergency_reports.id", ondelete="SET NULL"), nullable=True, index=True)
    device_id = Column(String(50), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, default="TELEMETRY")
    temperature = Column(Float, nullable=True)
    smoke_level = Column(Float, nullable=True)
    water_level = Column(Float, nullable=True)
    impact = Column(Float, nullable=True)
    acceleration_magnitude_g = Column(Float, nullable=True)
    alert_qualified = Column(Boolean, nullable=False, default=False)
    simulated = Column(Boolean, nullable=False, default=False)
    firmware_version = Column(String(32), nullable=True)
    wifi_connected = Column(Boolean, nullable=True)
    uptime_ms = Column(BigInteger, nullable=True)
    mpu6050_available = Column(Boolean, nullable=True)
    dht22_available = Column(Boolean, nullable=True)
    mq2_available = Column(Boolean, nullable=True)
    mq2_warmed = Column(Boolean, nullable=True)
    mq2_calibrated = Column(Boolean, nullable=True)
    humidity_percent = Column(Float, nullable=True)
    mq2_raw_adc = Column(Integer, nullable=True)
    mq2_filtered_adc = Column(Integer, nullable=True)
    mq2_baseline_adc = Column(Integer, nullable=True)
    acceleration_magnitude_mps2 = Column(Float, nullable=True)
    dynamic_acceleration_g = Column(Float, nullable=True)
    vibration_rms_g = Column(Float, nullable=True)
    gyro_x_dps = Column(Float, nullable=True)
    gyro_y_dps = Column(Float, nullable=True)
    gyro_z_dps = Column(Float, nullable=True)
    hazard_severity = Column(String(20), nullable=True)
    source_sensor = Column(String(50), nullable=True)
    observed_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    measurement_unit = Column(String(24), nullable=True)
    reason = Column(String(120), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    device_timestamp = Column(DateTime(timezone=True), nullable=True)
    water_level_raw_adc = Column(Integer, nullable=True)
    fsr_raw_adc = Column(Integer, nullable=True)
    signal_quality = Column(Integer, nullable=True)  # GSM CSQ 0-31 (99 = unknown) from AT+CSQ
    created_incident = Column(Boolean, default=False, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    incident = relationship("EmergencyReport", back_populates="sensor_readings")


class Device(Base):
    __tablename__ = "iot_devices"

    device_id = Column(String(50), primary_key=True)
    name = Column(String(150), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_label = Column(String(255), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    firmware_version = Column(String(32), nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    last_transport = Column(String(10), nullable=True)
    last_signal_quality = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
