from sqlalchemy.ext.asyncio import AsyncSession

from app.embeddings.provider import EmbeddingProvider
from app.reranking.provider import Reranker
from app.retrieval.dense import dense_search
from app.retrieval.fusion import fuse_and_rank
from app.retrieval.schemas import RetrievalResult, RetrievedChunk
from app.retrieval.sparse import sparse_search


class RetrievalService:
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        reranker: Reranker,
        candidate_limit: int = 20,
        top_k: int = 5,
        rrf_k: int = 60,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._reranker = reranker
        self._candidate_limit = candidate_limit
        self._top_k = top_k
        self._rrf_k = rrf_k

    async def search(
        self,
        session: AsyncSession,
        query: str,
        category: str | None = None,
    ) -> RetrievalResult:
        [query_embedding] = await self._embedding_provider.embed([query])

        dense_results = await dense_search(session, query_embedding, self._candidate_limit, category)
        sparse_results = await sparse_search(session, query, self._candidate_limit, category)

        by_id = {str(chunk.id): chunk for chunk in [*dense_results, *sparse_results]}
        dense_ids = [str(chunk.id) for chunk in dense_results]
        sparse_ids = [str(chunk.id) for chunk in sparse_results]
        fused = fuse_and_rank([dense_ids, sparse_ids], k=self._rrf_k)

        candidates = [(by_id[chunk_id], score) for chunk_id, score in fused if chunk_id in by_id]
        if not candidates:
            return RetrievalResult(query=query, chunks=[])

        rerank_scores = await self._reranker.rerank(query, [chunk.content for chunk, _ in candidates])

        reranked = sorted(
            zip(candidates, rerank_scores, strict=True),
            key=lambda pair: pair[1],
            reverse=True,
        )

        chunks = [
            RetrievedChunk(
                document=chunk.document,
                category=chunk.category,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                fused_score=fused_score,
                rerank_score=rerank_score,
            )
            for (chunk, fused_score), rerank_score in reranked[: self._top_k]
        ]
        return RetrievalResult(query=query, chunks=chunks)
