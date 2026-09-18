from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DocumentChunkRecord
from app.knowledge.schemas import DocumentChunk


async def replace_document_chunks(
    session: AsyncSession,
    document: str,
    chunks: list[DocumentChunk],
    embeddings: list[list[float]],
) -> None:
    await session.execute(delete(DocumentChunkRecord).where(DocumentChunkRecord.document == document))
    for chunk, embedding in zip(chunks, embeddings, strict=True):
        session.add(
            DocumentChunkRecord(
                document=chunk.document,
                category=chunk.category,
                source=chunk.source,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                embedding=embedding,
            )
        )
    await session.commit()


async def count_document_chunks(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(DocumentChunkRecord))
    return result.scalar_one()
