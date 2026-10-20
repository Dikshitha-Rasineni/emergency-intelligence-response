"""store filtered MQ-2 ADC count separately from raw sample

Revision ID: b72f308a45c1
Revises: a41c9e7b3d20
Create Date: 2026-10-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b72f308a45c1"
down_revision: Union[str, Sequence[str], None] = "a41c9e7b3d20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sensor_readings", sa.Column("mq2_filtered_adc", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("sensor_readings", "mq2_filtered_adc")
