from types import SimpleNamespace
from unittest.mock import AsyncMock

import groq
import httpx
import pytest

from app.llm.exceptions import LLMError
from app.llm.groq_provider import GroqProvider
from app.llm.schemas import ChatMessage


def make_chat_completion(content: str, finish_reason: str = "stop", usage: tuple[int, int, int] | None = (10, 5, 15)):
    usage_obj = None
    if usage is not None:
        prompt_tokens, completion_tokens, total_tokens = usage
        usage_obj = SimpleNamespace(
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, total_tokens=total_tokens
        )
    choice = SimpleNamespace(message=SimpleNamespace(content=content), finish_reason=finish_reason)
    return SimpleNamespace(choices=[choice], model="openai/gpt-oss-20b", usage=usage_obj)


async def fake_chunk_stream(chunks: list[str]):
    for chunk in chunks:
        yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=chunk))])


def make_rate_limit_error() -> groq.RateLimitError:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(429, request=request)
    return groq.RateLimitError("rate limited", response=response, body=None)


@pytest.fixture
def provider() -> GroqProvider:
    return GroqProvider(api_key="test-key", model="openai/gpt-oss-20b")


@pytest.mark.asyncio
async def test_complete_returns_llm_response(provider: GroqProvider):
    provider._client.chat.completions.create = AsyncMock(return_value=make_chat_completion("hello"))

    result = await provider.complete([ChatMessage(role="user", content="hi")])

    assert result.content == "hello"
    assert result.finish_reason == "stop"
    assert result.usage.total_tokens == 15


@pytest.mark.asyncio
async def test_complete_handles_missing_usage(provider: GroqProvider):
    provider._client.chat.completions.create = AsyncMock(
        return_value=make_chat_completion("hello", usage=None)
    )

    result = await provider.complete([ChatMessage(role="user", content="hi")])

    assert result.usage.total_tokens == 0


@pytest.mark.asyncio
async def test_complete_passes_json_mode_as_response_format(provider: GroqProvider):
    create = AsyncMock(return_value=make_chat_completion('{"a": 1}'))
    provider._client.chat.completions.create = create

    await provider.complete([ChatMessage(role="user", content="hi")], json_mode=True)

    assert create.call_args.kwargs["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_complete_wraps_groq_error(provider: GroqProvider):
    provider._client.chat.completions.create = AsyncMock(side_effect=make_rate_limit_error())

    with pytest.raises(LLMError):
        await provider.complete([ChatMessage(role="user", content="hi")])


@pytest.mark.asyncio
async def test_stream_yields_deltas(provider: GroqProvider):
    provider._client.chat.completions.create = AsyncMock(
        return_value=fake_chunk_stream(["Hel", "lo", "!"])
    )

    chunks = [c async for c in provider.stream([ChatMessage(role="user", content="hi")])]

    assert chunks == ["Hel", "lo", "!"]


@pytest.mark.asyncio
async def test_stream_wraps_groq_error(provider: GroqProvider):
    provider._client.chat.completions.create = AsyncMock(side_effect=make_rate_limit_error())

    with pytest.raises(LLMError):
        async for _ in provider.stream([ChatMessage(role="user", content="hi")]):
            pass
