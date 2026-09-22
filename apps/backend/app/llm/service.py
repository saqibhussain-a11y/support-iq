import json
from collections.abc import AsyncIterator, Callable
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.exceptions import LLMError
from app.llm.provider import ModelProvider
from app.llm.schemas import ChatMessage, LLMResponse, TokenUsage

T = TypeVar("T", bound=BaseModel)

UsageListener = Callable[[TokenUsage], None]


class LLMService:
    def __init__(self, provider: ModelProvider) -> None:
        self._provider = provider

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        top_p: float = 1.0,
        tools: list[dict] | None = None,
        on_usage: UsageListener | None = None,
    ) -> LLMResponse:
        response = await self._provider.complete(messages, temperature=temperature, top_p=top_p, tools=tools)
        if on_usage:
            on_usage(response.usage)
        return response

    async def complete_structured(
        self,
        messages: list[ChatMessage],
        schema: type[T],
        *,
        temperature: float = 0.7,
        top_p: float = 1.0,
        on_usage: UsageListener | None = None,
    ) -> T:
        response = await self._provider.complete(
            messages, temperature=temperature, top_p=top_p, json_mode=True
        )
        if on_usage:
            on_usage(response.usage)
        try:
            return schema.model_validate_json(response.content)
        except (ValidationError, json.JSONDecodeError) as exc:
            raise LLMError(f"LLM response did not match {schema.__name__}: {exc}") from exc

    def stream(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        top_p: float = 1.0,
    ) -> AsyncIterator[str]:
        return self._provider.stream(messages, temperature=temperature, top_p=top_p)
