from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.embeddings.provider import EmbeddingProvider
from app.reranking.provider import Reranker
from app.retrieval.service import RetrievalService


class FakeEmbeddingProvider(EmbeddingProvider):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeReranker(Reranker):
    def __init__(self, score_map: dict[str, float]) -> None:
        self.score_map = score_map

    async def rerank(self, query: str, documents: list[str]) -> list[float]:
        return [self.score_map.get(doc, 0.0) for doc in documents]


def make_chunk(chunk_id: str, document: str, content: str):
    return SimpleNamespace(id=chunk_id, document=document, category="billing", chunk_index=0, content=content)


@pytest.mark.asyncio
async def test_search_fuses_dense_and_sparse_then_reranks():
    dense_chunk = make_chunk("1", "duplicate_charges.md", "duplicate charge content")
    sparse_chunk = make_chunk("2", "refund_policy.md", "refund policy content")

    reranker = FakeReranker(
        {
            "duplicate charge content": 0.5,
            "refund policy content": 0.9,
        }
    )
    service = RetrievalService(embedding_provider=FakeEmbeddingProvider(), reranker=reranker)

    with (
        patch("app.retrieval.service.dense_search", new=AsyncMock(return_value=[dense_chunk])),
        patch("app.retrieval.service.sparse_search", new=AsyncMock(return_value=[sparse_chunk])),
    ):
        result = await service.search(session=object(), query="charged twice")

    assert result.query == "charged twice"
    assert len(result.chunks) == 2
    assert result.chunks[0].document == "refund_policy.md"
    assert result.chunks[1].document == "duplicate_charges.md"


@pytest.mark.asyncio
async def test_search_deduplicates_chunk_appearing_in_both_dense_and_sparse():
    shared_chunk = make_chunk("1", "refund_policy.md", "shared content")

    reranker = FakeReranker({"shared content": 1.0})
    service = RetrievalService(embedding_provider=FakeEmbeddingProvider(), reranker=reranker)

    with (
        patch("app.retrieval.service.dense_search", new=AsyncMock(return_value=[shared_chunk])),
        patch("app.retrieval.service.sparse_search", new=AsyncMock(return_value=[shared_chunk])),
    ):
        result = await service.search(session=object(), query="q")

    assert len(result.chunks) == 1


@pytest.mark.asyncio
async def test_search_returns_empty_when_no_candidates():
    service = RetrievalService(embedding_provider=FakeEmbeddingProvider(), reranker=FakeReranker({}))

    with (
        patch("app.retrieval.service.dense_search", new=AsyncMock(return_value=[])),
        patch("app.retrieval.service.sparse_search", new=AsyncMock(return_value=[])),
    ):
        result = await service.search(session=object(), query="q")

    assert result.chunks == []


@pytest.mark.asyncio
async def test_search_respects_top_k():
    chunks = [make_chunk(str(i), f"doc{i}.md", f"content{i}") for i in range(5)]
    reranker = FakeReranker({f"content{i}": float(i) for i in range(5)})
    service = RetrievalService(embedding_provider=FakeEmbeddingProvider(), reranker=reranker, top_k=2)

    with (
        patch("app.retrieval.service.dense_search", new=AsyncMock(return_value=chunks)),
        patch("app.retrieval.service.sparse_search", new=AsyncMock(return_value=[])),
    ):
        result = await service.search(session=object(), query="q")

    assert len(result.chunks) == 2
    assert result.chunks[0].document == "doc4.md"
