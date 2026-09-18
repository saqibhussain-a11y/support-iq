from abc import ABC, abstractmethod


class Reranker(ABC):
    @abstractmethod
    async def rerank(self, query: str, documents: list[str]) -> list[float]: ...
