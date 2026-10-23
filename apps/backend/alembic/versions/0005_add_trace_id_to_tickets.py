"""add trace_id to tickets

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tickets", sa.Column("trace_id", sa.String(32), nullable=True))


def downgrade() -> None:
    op.drop_column("tickets", "trace_id")
