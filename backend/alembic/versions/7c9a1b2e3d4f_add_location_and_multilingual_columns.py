"""add_location_and_multilingual_columns

Revision ID: 7c9a1b2e3d4f
Revises: 256a96bd5612
Create Date: 2026-10-17 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c9a1b2e3d4f'
down_revision: Union[str, Sequence[str], None] = '256a96bd5612'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Allow nullable latitude and longitude on emergency_reports
    op.execute("ALTER TABLE emergency_reports ALTER COLUMN latitude DROP NOT NULL")
    op.execute("ALTER TABLE emergency_reports ALTER COLUMN longitude DROP NOT NULL")

    # 2. Add location_source, coordinates_verified, and detected_language columns safely
    op.execute("ALTER TABLE emergency_reports ADD COLUMN IF NOT EXISTS location_source VARCHAR(50) DEFAULT 'USER_ENTERED'")
    op.execute("ALTER TABLE emergency_reports ADD COLUMN IF NOT EXISTS coordinates_verified BOOLEAN DEFAULT TRUE")
    op.execute("ALTER TABLE emergency_reports ADD COLUMN IF NOT EXISTS detected_language VARCHAR(20) DEFAULT 'en'")


def downgrade() -> None:
    op.execute("ALTER TABLE emergency_reports DROP COLUMN IF EXISTS detected_language")
    op.execute("ALTER TABLE emergency_reports DROP COLUMN IF EXISTS coordinates_verified")
    op.execute("ALTER TABLE emergency_reports DROP COLUMN IF EXISTS location_source")
