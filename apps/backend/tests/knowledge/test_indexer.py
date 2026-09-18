from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.embeddings.provider import EmbeddingProvider
from app.knowledge.indexer import build_document_chunks, index_knowledge_base
from app.knowledge.schemas import RawDocument


class FakeEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        self.embedded_texts: list[str] = []

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.embedded_texts.extend(texts)
        return [[0.1, 0.2] for _ in texts]


def test_build_document_chunks_carries_metadata():
    raw = RawDocument(
        document="refund_policy.md",
        category="refunds",
        text="# Refund Policy\n\n## Eligibility\n\nSome text.",
    )

    chunks = build_document_chunks(raw)

    assert len(chunks) == 1
    assert chunks[0].document == "refund_policy.md"
    assert chunks[0].category == "refunds"
    assert chunks[0].source == "knowledge_base"
    assert chunks[0].chunk_index == 0


def test_build_document_chunks_indexes_sequentially():
    raw = RawDocument(
        document="doc.md",
        category="support",
        text="# Doc\n\n## One\n\nContent.\n\n## Two\n\nContent.",
    )

    chunks = build_document_chunks(raw)

    assert [chunk.chunk_index for chunk in chunks] == [0, 1]


@pytest.mark.asyncio
async def test_index_knowledge_base_orchestrates_pipeline(tmp_path: Path):
    billing_dir = tmp_path / "billing"
    billing_dir.mkdir()
    (billing_dir / "doc.md").write_text(
        "# Doc\n\n## Section One\n\nContent one.\n\n## Section Two\n\nContent two."
    )

    provider = FakeEmbeddingProvider()

    with (
        patch("app.knowledge.indexer.replace_document_chunks", new=AsyncMock()) as mock_replace,
        patch("app.knowledge.indexer.count_document_chunks", new=AsyncMock(return_value=2)) as mock_count,
    ):
        result = await index_knowledge_base(
            session=object(), embedding_provider=provider, knowledge_base_path=tmp_path
        )

    assert result.documents_processed == 1
    assert result.chunks_created == 2
    assert result.chunks_embedded == 2
    assert result.total_chunks_in_store == 2
    assert mock_replace.await_count == 1
    assert mock_count.await_count == 1
    assert len(provider.embedded_texts) == 2


@pytest.mark.asyncio
async def test_index_knowledge_base_skips_documents_with_no_chunks(tmp_path: Path):
    billing_dir = tmp_path / "billing"
    billing_dir.mkdir()
    (billing_dir / "empty.md").write_text("# Title\n\n")

    provider = FakeEmbeddingProvider()

    with (
        patch("app.knowledge.indexer.replace_document_chunks", new=AsyncMock()) as mock_replace,
        patch("app.knowledge.indexer.count_document_chunks", new=AsyncMock(return_value=0)),
    ):
        result = await index_knowledge_base(
            session=object(), embedding_provider=provider, knowledge_base_path=tmp_path
        )

    assert result.documents_processed == 0
    assert result.chunks_created == 0
    mock_replace.assert_not_awaited()
