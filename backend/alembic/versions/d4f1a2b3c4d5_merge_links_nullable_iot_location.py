"""incident merge links; IoT readings may lack coordinates

Revision ID: d4f1a2b3c4d5
Revises: c3e9d1f0a7b2
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "d4f1a2b3c4d5"
down_revision: Union[str, Sequence[str], None] = "c3e9d1f0a7b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("emergency_reports", sa.Column("merged_into_id", sa.String(length=50), nullable=True))
    op.create_index("ix_emergency_reports_merged_into_id", "emergency_reports", ["merged_into_id"])
    op.create_foreign_key("fk_emergency_reports_merged_into", "emergency_reports", "emergency_reports",
                          ["merged_into_id"], ["id"], ondelete="SET NULL")
    op.alter_column("sensor_readings", "latitude", existing_type=sa.Float(), nullable=True)
    op.alter_column("sensor_readings", "longitude", existing_type=sa.Float(), nullable=True)


def downgrade() -> None:
    op.execute("DELETE FROM sensor_readings WHERE latitude IS NULL OR longitude IS NULL")
    op.alter_column("sensor_readings", "longitude", existing_type=sa.Float(), nullable=False)
    op.alter_column("sensor_readings", "latitude", existing_type=sa.Float(), nullable=False)
    op.drop_constraint("fk_emergency_reports_merged_into", "emergency_reports", type_="foreignkey")
    op.drop_index("ix_emergency_reports_merged_into_id", table_name="emergency_reports")
    op.drop_column("emergency_reports", "merged_into_id")
