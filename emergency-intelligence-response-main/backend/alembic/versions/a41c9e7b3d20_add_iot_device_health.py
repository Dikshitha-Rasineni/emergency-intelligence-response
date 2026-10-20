"""persist IoT device connectivity and sensor availability

Revision ID: a41c9e7b3d20
Revises: 8d4f6a1c2b90
Create Date: 2026-10-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a41c9e7b3d20"
down_revision: Union[str, Sequence[str], None] = "8d4f6a1c2b90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sensor_readings", sa.Column("firmware_version", sa.String(length=32), nullable=True))
    op.add_column("sensor_readings", sa.Column("wifi_connected", sa.Boolean(), nullable=True))
    op.add_column("sensor_readings", sa.Column("uptime_ms", sa.BigInteger(), nullable=True))
    op.add_column("sensor_readings", sa.Column("mpu6050_available", sa.Boolean(), nullable=True))
    op.add_column("sensor_readings", sa.Column("dht22_available", sa.Boolean(), nullable=True))
    op.add_column("sensor_readings", sa.Column("mq2_available", sa.Boolean(), nullable=True))
    op.add_column("sensor_readings", sa.Column("mq2_warmed", sa.Boolean(), nullable=True))
    op.add_column("sensor_readings", sa.Column("mq2_calibrated", sa.Boolean(), nullable=True))


def downgrade() -> None:
    for column in (
        "mq2_calibrated", "mq2_warmed", "mq2_available", "dht22_available",
        "mpu6050_available", "uptime_ms", "wifi_connected", "firmware_version",
    ):
        op.drop_column("sensor_readings", column)
