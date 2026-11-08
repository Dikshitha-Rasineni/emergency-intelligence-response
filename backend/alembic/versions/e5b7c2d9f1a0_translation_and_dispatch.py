"""machine translation fields, translated citizen notes, response units and dispatches

Revision ID: e5b7c2d9f1a0
Revises: d4f1a2b3c4d5
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "e5b7c2d9f1a0"
down_revision: Union[str, Sequence[str], None] = "d4f1a2b3c4d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("emergency_reports", sa.Column("english_translation", sa.Text(), nullable=True))
    op.add_column("emergency_reports", sa.Column("translation_provider", sa.String(length=60), nullable=True))
    op.add_column("incident_updates", sa.Column("note_translated", sa.Text(), nullable=True))
    op.add_column("incident_updates", sa.Column("note_language", sa.String(length=20), nullable=True))

    op.create_table(
        "response_units",
        sa.Column("id", sa.String(length=30), primary_key=True),
        sa.Column("call_sign", sa.String(length=80), nullable=False),
        sa.Column("unit_type", sa.String(length=30), nullable=False),
        sa.Column("department", sa.String(length=20), nullable=False),
        sa.Column("base_resource_id", sa.String(length=50),
                  sa.ForeignKey("emergency_resources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("position_source", sa.String(length=20), nullable=False, server_default="STATION"),
        sa.Column("position_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="AVAILABLE"),
        sa.Column("capabilities", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("crew_token_hash", sa.String(length=128), nullable=True),
        sa.Column("data_source", sa.String(length=30), nullable=False, server_default="DEMO_SEED"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_response_units_department", "response_units", ["department"])
    op.create_index("ix_response_units_status", "response_units", ["status"])

    op.create_table(
        "dispatches",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("incident_id", sa.String(length=50), sa.ForeignKey("emergency_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unit_id", sa.String(length=30), sa.ForeignKey("response_units.id", ondelete="CASCADE"), nullable=False),
        sa.Column("department", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ASSIGNED"),
        sa.Column("auto", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("assigned_by", sa.String(length=150), nullable=True),
        sa.Column("origin_lat", sa.Float(), nullable=True),
        sa.Column("origin_lng", sa.Float(), nullable=True),
        sa.Column("distance_km", sa.Float(), nullable=True),
        sa.Column("eta_min", sa.Float(), nullable=True),
        sa.Column("eta_source", sa.String(length=40), nullable=True),
        sa.Column("route", sa.JSON(), nullable=True),
        sa.Column("destination_resource_id", sa.String(length=50),
                  sa.ForeignKey("emergency_resources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("en_route_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("on_scene_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("transporting_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("history", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.create_index("ix_dispatches_incident_id", "dispatches", ["incident_id"])
    op.create_index("ix_dispatches_unit_id", "dispatches", ["unit_id"])
    op.create_index("ix_dispatches_department", "dispatches", ["department"])
    op.create_index("ix_dispatches_status", "dispatches", ["status"])


def downgrade() -> None:
    op.drop_table("dispatches")
    op.drop_table("response_units")
    op.drop_column("incident_updates", "note_language")
    op.drop_column("incident_updates", "note_translated")
    op.drop_column("emergency_reports", "translation_provider")
    op.drop_column("emergency_reports", "english_translation")
