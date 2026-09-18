from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DocumentChunkRecord


async def dense_search(
    session: AsyncSession,
    query_embedding: list[float],
    limit: int,
    category: str | None = None,
) -> list[DocumentChunkRecord]:
    stmt = select(DocumentChunkRecord).order_by(
        DocumentChunkRecord.embedding.cosine_distance(query_embedding)
    )
    if category is not None:
        stmt = stmt.where(DocumentChunkRecord.category == category)
    stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    return list(result.scalars().all())
