from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.llm.schemas import ChatMessage, LLMResponse


class ModelProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        top_p: float = 1.0,
        json_mode: bool = False,
        tools: list[dict] | None = None,
    ) -> LLMResponse: ...

    @abstractmethod
    def stream(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        top_p: float = 1.0,
    ) -> AsyncIterator[str]: ...
