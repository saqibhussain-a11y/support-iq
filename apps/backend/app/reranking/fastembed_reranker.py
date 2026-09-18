import asyncio

from fastembed.rerank.cross_encoder import TextCrossEncoder

from app.reranking.provider import Reranker


class FastEmbedReranker(Reranker):
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model: TextCrossEncoder | None = None

    def _get_model(self) -> TextCrossEncoder:
        if self._model is None:
            self._model = TextCrossEncoder(model_name=self._model_name)
        return self._model

    async def rerank(self, query: str, documents: list[str]) -> list[float]:
        return await asyncio.to_thread(self._rerank_sync, query, documents)

    def _rerank_sync(self, query: str, documents: list[str]) -> list[float]:
        model = self._get_model()
        return list(model.rerank(query, documents))
