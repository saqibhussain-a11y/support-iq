from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DocumentChunkRecord


async def fetch_full_document(session: AsyncSession, document_name: str) -> str | None:
    query = (
        select(DocumentChunkRecord.content)
        .where(DocumentChunkRecord.document == document_name)
        .order_by(DocumentChunkRecord.chunk_index)
    )
    result = await session.execute(query)
    rows = result.scalars().all()
    if not rows:
        return None
    return "\n\n".join(rows)
