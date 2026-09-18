from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DocumentChunkRecord


async def sparse_search(
    session: AsyncSession,
    query_text: str,
    limit: int,
    category: str | None = None,
) -> list[DocumentChunkRecord]:
    tsquery = func.plainto_tsquery("english", query_text)
    stmt = select(DocumentChunkRecord).where(DocumentChunkRecord.content_tsv.op("@@")(tsquery))
    if category is not None:
        stmt = stmt.where(DocumentChunkRecord.category == category)
    stmt = stmt.order_by(func.ts_rank(DocumentChunkRecord.content_tsv, tsquery).desc()).limit(limit)

    result = await session.execute(stmt)
    return list(result.scalars().all())
