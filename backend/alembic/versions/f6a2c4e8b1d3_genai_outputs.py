"""GenAI outputs cache on incidents (briefs, citizen guidance)

Revision ID: f6a2c4e8b1d3
Revises: e5b7c2d9f1a0
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f6a2c4e8b1d3"
down_revision: Union[str, Sequence[str], None] = "e5b7c2d9f1a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("emergency_reports", sa.Column("genai", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("emergency_reports", "genai")
