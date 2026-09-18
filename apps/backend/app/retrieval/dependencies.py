from functools import lru_cache

from app.core.config import get_settings
from app.embeddings.dependencies import get_embedding_provider
from app.reranking.dependencies import get_reranker
from app.retrieval.service import RetrievalService


@lru_cache
def get_retrieval_service() -> RetrievalService:
    settings = get_settings()
    return RetrievalService(
        embedding_provider=get_embedding_provider(),
        reranker=get_reranker(),
        candidate_limit=settings.retrieval_candidate_limit,
        top_k=settings.retrieval_top_k,
        rrf_k=settings.rrf_k,
    )
