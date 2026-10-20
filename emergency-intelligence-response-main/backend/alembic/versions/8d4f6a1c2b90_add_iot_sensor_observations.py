"""store raw IoT measurements and preliminary alert metadata

Revision ID: 8d4f6a1c2b90
Revises: 7c9a1b2e3d4f
Create Date: 2026-10-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "8d4f6a1c2b90"
down_revision: Union[str, Sequence[str], None] = "7c9a1b2e3d4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sensor_readings", sa.Column("humidity_percent", sa.Float(), nullable=True))
    op.add_column("sensor_readings", sa.Column("acceleration_magnitude_g", sa.Float(), nullable=True))
    op.add_column("sensor_readings", sa.Column("alert_qualified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("sensor_readings", sa.Column("simulated", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("sensor_readings", sa.Column("mq2_raw_adc", sa.Integer(), nullable=True))
    op.add_column("sensor_readings", sa.Column("mq2_baseline_adc", sa.Integer(), nullable=True))
    op.add_column("sensor_readings", sa.Column("acceleration_magnitude_mps2", sa.Float(), nullable=True))
    op.add_column("sensor_readings", sa.Column("dynamic_acceleration_g", sa.Float(), nullable=True))
    op.add_column("sensor_readings", sa.Column("vibration_rms_g", sa.Float(), nullable=True))
    op.add_column("sensor_readings", sa.Column("gyro_x_dps", sa.Float(), nullable=True))
    op.add_column("sensor_readings", sa.Column("gyro_y_dps", sa.Float(), nullable=True))
    op.add_column("sensor_readings", sa.Column("gyro_z_dps", sa.Float(), nullable=True))
    op.add_column("sensor_readings", sa.Column("hazard_severity", sa.String(length=20), nullable=True))
    op.add_column("sensor_readings", sa.Column("source_sensor", sa.String(length=50), nullable=True))
    op.add_column("sensor_readings", sa.Column("observed_value", sa.Float(), nullable=True))
    op.add_column("sensor_readings", sa.Column("threshold_value", sa.Float(), nullable=True))
    op.add_column("sensor_readings", sa.Column("measurement_unit", sa.String(length=24), nullable=True))
    op.add_column("sensor_readings", sa.Column("reason", sa.String(length=120), nullable=True))


def downgrade() -> None:
    for column in (
        "reason", "measurement_unit", "threshold_value", "observed_value", "source_sensor",
        "hazard_severity", "gyro_z_dps", "gyro_y_dps", "gyro_x_dps", "vibration_rms_g",
        "dynamic_acceleration_g", "acceleration_magnitude_mps2", "mq2_baseline_adc",
        "mq2_raw_adc", "simulated", "alert_qualified", "acceleration_magnitude_g", "humidity_percent",
    ):
        op.drop_column("sensor_readings", column)
