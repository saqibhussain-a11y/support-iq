import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, Integer, String, Text
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.embeddings.provider import EMBEDDING_DIMENSION


class DocumentChunkRecord(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="knowledge_base")
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSION), nullable=False)
    content_tsv: Mapped[str] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', content)", persisted=True), nullable=True
    )
