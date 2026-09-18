from functools import lru_cache

from app.core.config import get_settings
from app.reranking.fastembed_reranker import FastEmbedReranker
from app.reranking.provider import Reranker


@lru_cache
def get_reranker() -> Reranker:
    settings = get_settings()
    return FastEmbedReranker(model_name=settings.reranker_model)
