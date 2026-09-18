from abc import ABC, abstractmethod

EMBEDDING_DIMENSION = 384


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
