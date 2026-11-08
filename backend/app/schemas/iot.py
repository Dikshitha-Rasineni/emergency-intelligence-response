from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class IoTEventCreate(BaseModel):
    device_id: str = Field(..., min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_.:-]+$", description="Unique ESP32 device ID")
    event_id: Optional[str] = Field(None, max_length=100, description="Device-unique event id (idempotency key), e.g. DEVICE:boot:seq")
    event_type: str = Field(default="TELEMETRY", pattern="^(TELEMETRY|ACCIDENT|FIRE|GAS|FLOOD|SOS)$",
                            description="TELEMETRY never creates an incident. Others require alert_qualified=true.")
    transport: Optional[str] = Field(None, pattern="^(WIFI|GPRS)$")
    water_level_raw_adc: Optional[int] = Field(None, ge=0, le=4095)
    fsr_raw_adc: Optional[int] = Field(None, ge=0, le=4095)
    signal_quality: Optional[int] = Field(None, ge=0, le=99, description="GSM signal (AT+CSQ, 0-31; 99 unknown)")
    temperature: Optional[float] = Field(None, ge=-40.0, le=150.0, description="Temperature in Celsius")
    smoke_level: Optional[float] = Field(None, ge=0.0, le=10000.0, description="Smoke/gas sensor PPM")
    water_level: Optional[float] = Field(None, ge=0.0, le=500.0, description="Water level in cm")
    impact: Optional[float] = Field(None, ge=0.0, le=50.0, description="Impact acceleration in Gs")
    acceleration_magnitude_g: Optional[float] = Field(None, ge=0.0, le=50.0)
    alert_qualified: bool = Field(default=False, description="True only after device-side persistence/confirmation rules pass")
    simulated: bool = Field(default=False, description="Mock data; stored for testing and never incident-triggering")
    firmware_version: Optional[str] = Field(None, max_length=32)
    wifi_connected: Optional[bool] = None
    uptime_ms: Optional[int] = Field(None, ge=0, le=4294967295)
    mpu6050_available: Optional[bool] = None
    dht22_available: Optional[bool] = None
    mq2_available: Optional[bool] = None
    mq2_warmed: Optional[bool] = None
    mq2_calibrated: Optional[bool] = None
    humidity_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    mq2_raw_adc: Optional[int] = Field(None, ge=0, le=4095, description="Raw ADC counts; not ppm")
    mq2_filtered_adc: Optional[int] = Field(None, ge=0, le=4095, description="Smoothed ADC counts; not ppm")
    mq2_baseline_adc: Optional[int] = Field(None, ge=0, le=4095, description="Calibrated baseline ADC counts")
    acceleration_magnitude_mps2: Optional[float] = Field(None, ge=0.0, le=200.0)
    dynamic_acceleration_g: Optional[float] = Field(None, ge=0.0, le=50.0)
    vibration_rms_g: Optional[float] = Field(None, ge=0.0, le=50.0)
    gyro_x_dps: Optional[float] = Field(None, ge=-4000.0, le=4000.0)
    gyro_y_dps: Optional[float] = Field(None, ge=-4000.0, le=4000.0)
    gyro_z_dps: Optional[float] = Field(None, ge=-4000.0, le=4000.0)
    hazard_severity: Optional[str] = Field(None, max_length=20)
    source_sensor: Optional[str] = Field(None, max_length=50)
    observed_value: Optional[float] = None
    threshold_value: Optional[float] = None
    measurement_unit: Optional[str] = Field(None, max_length=24)
    reason: Optional[str] = Field(None, max_length=120)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Omit to use the registered device location")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    timestamp: Optional[datetime] = None


class IoTEventResponse(BaseModel):
    reading_id: str
    device_id: str
    event_type: str
    event_id: Optional[str] = None
    status: str  # STORED | INCIDENT_CREATED | MERGED_INTO_INCIDENT | DUPLICATE | REJECTED_NO_LOCATION
    incident_id: Optional[str] = None
    priority_score: Optional[int] = None
    severity: Optional[str] = None
    message: str


class DeviceUpsert(BaseModel):
    device_id: str = Field(..., min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_.:-]+$")
    name: Optional[str] = Field(None, max_length=150)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    location_label: Optional[str] = Field(None, max_length=255)
    active: bool = True
