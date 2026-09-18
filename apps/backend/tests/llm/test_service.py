from collections.abc import AsyncIterator

import pytest
from pydantic import BaseModel

from app.llm.exceptions import LLMError
from app.llm.provider import ModelProvider
from app.llm.schemas import ChatMessage, LLMResponse, TokenUsage
from app.llm.service import LLMService


class Sentiment(BaseModel):
    label: str
    confidence: float


class FakeProvider(ModelProvider):
    def __init__(self, response: LLMResponse | None = None, chunks: list[str] | None = None) -> None:
        self.response = response
        self.chunks = chunks or []
        self.last_call_kwargs: dict | None = None

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        top_p: float = 1.0,
        json_mode: bool = False,
    ) -> LLMResponse:
        self.last_call_kwargs = {"temperature": temperature, "top_p": top_p, "json_mode": json_mode}
        assert self.response is not None
        return self.response

    async def stream(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        top_p: float = 1.0,
    ) -> AsyncIterator[str]:
        for chunk in self.chunks:
            yield chunk


def make_response(content: str) -> LLMResponse:
    return LLMResponse(
        content=content,
        model="llama-3.3-70b-versatile",
        finish_reason="stop",
        usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )


@pytest.mark.asyncio
async def test_complete_delegates_to_provider():
    provider = FakeProvider(response=make_response("hello"))
    service = LLMService(provider)

    result = await service.complete([ChatMessage(role="user", content="hi")])

    assert result.content == "hello"
    assert provider.last_call_kwargs == {"temperature": 0.7, "top_p": 1.0, "json_mode": False}


@pytest.mark.asyncio
async def test_complete_structured_parses_valid_json():
    provider = FakeProvider(response=make_response('{"label": "frustrated", "confidence": 0.9}'))
    service = LLMService(provider)

    result = await service.complete_structured([ChatMessage(role="user", content="hi")], Sentiment)

    assert result == Sentiment(label="frustrated", confidence=0.9)
    assert provider.last_call_kwargs is not None
    assert provider.last_call_kwargs["json_mode"] is True


@pytest.mark.asyncio
async def test_complete_structured_raises_on_invalid_json():
    provider = FakeProvider(response=make_response("not json"))
    service = LLMService(provider)

    with pytest.raises(LLMError):
        await service.complete_structured([ChatMessage(role="user", content="hi")], Sentiment)


@pytest.mark.asyncio
async def test_complete_structured_raises_on_schema_mismatch():
    provider = FakeProvider(response=make_response('{"unexpected": "field"}'))
    service = LLMService(provider)

    with pytest.raises(LLMError):
        await service.complete_structured([ChatMessage(role="user", content="hi")], Sentiment)


@pytest.mark.asyncio
async def test_stream_yields_provider_chunks():
    provider = FakeProvider(chunks=["Hel", "lo", "!"])
    service = LLMService(provider)

    chunks = [chunk async for chunk in service.stream([ChatMessage(role="user", content="hi")])]

    assert chunks == ["Hel", "lo", "!"]
