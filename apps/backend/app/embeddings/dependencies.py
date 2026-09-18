from functools import lru_cache

from app.core.config import get_settings
from app.embeddings.fastembed_provider import FastEmbedProvider
from app.embeddings.provider import EmbeddingProvider


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    return FastEmbedProvider(model_name=settings.embedding_model)
