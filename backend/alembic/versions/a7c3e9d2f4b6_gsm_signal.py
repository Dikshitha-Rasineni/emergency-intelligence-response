"""GSM signal quality from the in-car SIM unit

Revision ID: a7c3e9d2f4b6
Revises: f6a2c4e8b1d3
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7c3e9d2f4b6"
down_revision: Union[str, Sequence[str], None] = "f6a2c4e8b1d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sensor_readings", sa.Column("signal_quality", sa.Integer(), nullable=True))
    op.add_column("iot_devices", sa.Column("last_signal_quality", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("iot_devices", "last_signal_quality")
    op.drop_column("sensor_readings", "signal_quality")
