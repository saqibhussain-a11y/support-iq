from unittest.mock import MagicMock, patch

import pytest

from app.reranking.fastembed_reranker import FastEmbedReranker


@pytest.mark.asyncio
async def test_rerank_returns_scores_in_order():
    fake_model = MagicMock()
    fake_model.rerank.return_value = [0.2, 0.9, 0.5]

    with patch(
        "app.reranking.fastembed_reranker.TextCrossEncoder", return_value=fake_model
    ) as mock_cls:
        reranker = FastEmbedReranker(model_name="Xenova/ms-marco-MiniLM-L-6-v2")
        scores = await reranker.rerank("query", ["doc1", "doc2", "doc3"])

    assert scores == [0.2, 0.9, 0.5]
    mock_cls.assert_called_once_with(model_name="Xenova/ms-marco-MiniLM-L-6-v2")


@pytest.mark.asyncio
async def test_model_is_lazily_loaded_once():
    fake_model = MagicMock()
    fake_model.rerank.return_value = [0.1]

    with patch(
        "app.reranking.fastembed_reranker.TextCrossEncoder", return_value=fake_model
    ) as mock_cls:
        reranker = FastEmbedReranker(model_name="Xenova/ms-marco-MiniLM-L-6-v2")
        await reranker.rerank("q", ["a"])
        await reranker.rerank("q", ["b"])

    mock_cls.assert_called_once()
