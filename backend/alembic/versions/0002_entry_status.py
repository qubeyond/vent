"""add entries.status, entries.processing_error

Revision ID: 0002_entry_status
Revises: 0001_init_schema
Create Date: 2026-08-10

"""

import sqlalchemy as sa

from alembic import op

revision: str = "0002_entry_status"
down_revision: str | None = "0001_init_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "entries",
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ready"),
    )
    op.add_column("entries", sa.Column("processing_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("entries", "processing_error")
    op.drop_column("entries", "status")
