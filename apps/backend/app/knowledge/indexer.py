from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.embeddings.provider import EmbeddingProvider
from app.knowledge.chunker import chunk_markdown
from app.knowledge.loader import load_documents
from app.knowledge.repository import count_document_chunks, replace_document_chunks
from app.knowledge.schemas import DocumentChunk, IndexingResult, RawDocument


def build_document_chunks(raw_document: RawDocument) -> list[DocumentChunk]:
    pieces = chunk_markdown(raw_document.text)
    return [
        DocumentChunk(
            document=raw_document.document,
            category=raw_document.category,
            source="knowledge_base",
            chunk_index=index,
            content=piece,
        )
        for index, piece in enumerate(pieces)
    ]


async def index_knowledge_base(
    session: AsyncSession,
    embedding_provider: EmbeddingProvider,
    knowledge_base_path: Path,
) -> IndexingResult:
    raw_documents = load_documents(knowledge_base_path)

    documents_processed = 0
    chunks_created = 0
    chunks_embedded = 0

    for raw_document in raw_documents:
        chunks = build_document_chunks(raw_document)
        if not chunks:
            continue

        embeddings = await embedding_provider.embed([chunk.content for chunk in chunks])

        await replace_document_chunks(session, raw_document.document, chunks, embeddings)

        documents_processed += 1
        chunks_created += len(chunks)
        chunks_embedded += len(embeddings)

    total_chunks_in_store = await count_document_chunks(session)

    return IndexingResult(
        documents_processed=documents_processed,
        chunks_created=chunks_created,
        chunks_embedded=chunks_embedded,
        total_chunks_in_store=total_chunks_in_store,
    )
