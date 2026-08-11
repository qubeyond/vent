"""add entries.processing_stage

Revision ID: 0003_processing_stage
Revises: 0002_entry_status
Create Date: 2026-08-11

"""

import sqlalchemy as sa

from alembic import op

revision: str = "0003_processing_stage"
down_revision: str | None = "0002_entry_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("entries", sa.Column("processing_stage", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("entries", "processing_stage")
