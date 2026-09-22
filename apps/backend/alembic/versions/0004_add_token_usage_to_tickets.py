"""add token_usage to tickets

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-22

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tickets", sa.Column("token_usage", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("tickets", "token_usage")
