import asyncio

from fastembed import TextEmbedding

from app.embeddings.provider import EmbeddingProvider


class FastEmbedProvider(EmbeddingProvider):
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model: TextEmbedding | None = None

    def _get_model(self) -> TextEmbedding:
        if self._model is None:
            self._model = TextEmbedding(model_name=self._model_name)
        return self._model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(self._embed_sync, texts)

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        return [vector.tolist() for vector in model.embed(texts)]
