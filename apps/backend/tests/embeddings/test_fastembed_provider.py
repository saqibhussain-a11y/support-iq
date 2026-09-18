from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.embeddings.fastembed_provider import FastEmbedProvider


@pytest.mark.asyncio
async def test_embed_returns_lists_of_floats():
    fake_model = MagicMock()
    fake_model.embed.return_value = [np.array([0.1, 0.2, 0.3])]

    with patch("app.embeddings.fastembed_provider.TextEmbedding", return_value=fake_model) as mock_cls:
        provider = FastEmbedProvider(model_name="BAAI/bge-small-en-v1.5")
        result = await provider.embed(["hello"])

    assert result == [[0.1, 0.2, 0.3]]
    mock_cls.assert_called_once_with(model_name="BAAI/bge-small-en-v1.5")


@pytest.mark.asyncio
async def test_model_is_lazily_loaded_once():
    fake_model = MagicMock()
    fake_model.embed.return_value = [np.array([0.1])]

    with patch("app.embeddings.fastembed_provider.TextEmbedding", return_value=fake_model) as mock_cls:
        provider = FastEmbedProvider(model_name="BAAI/bge-small-en-v1.5")
        await provider.embed(["a"])
        await provider.embed(["b"])

    mock_cls.assert_called_once()
