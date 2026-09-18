"""add content_tsv for full-text search

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import TSVECTOR

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "document_chunks",
        sa.Column(
            "content_tsv",
            TSVECTOR,
            sa.Computed("to_tsvector('english', content)", persisted=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_document_chunks_content_tsv",
        "document_chunks",
        ["content_tsv"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_document_chunks_content_tsv", table_name="document_chunks")
    op.drop_column("document_chunks", "content_tsv")
