import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import groq
import httpx
import pytest

from app.llm.exceptions import LLMError
from app.llm.groq_provider import GroqProvider
from app.llm.schemas import ChatMessage, ToolCall


def make_chat_completion(
    content: str | None,
    finish_reason: str = "stop",
    usage: tuple[int, int, int] | None = (10, 5, 15),
    tool_calls=None,
):
    usage_obj = None
    if usage is not None:
        prompt_tokens, completion_tokens, total_tokens = usage
        usage_obj = SimpleNamespace(
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, total_tokens=total_tokens
        )
    choice = SimpleNamespace(
        message=SimpleNamespace(content=content, tool_calls=tool_calls), finish_reason=finish_reason
    )
    return SimpleNamespace(choices=[choice], model="openai/gpt-oss-20b", usage=usage_obj)


def make_api_tool_call(call_id: str, name: str, arguments: dict):
    return SimpleNamespace(
        id=call_id, type="function", function=SimpleNamespace(name=name, arguments=json.dumps(arguments))
    )


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
async def test_complete_passes_tools_and_tool_choice_when_tools_given(provider: GroqProvider):
    create = AsyncMock(return_value=make_chat_completion("hello"))
    provider._client.chat.completions.create = create
    tools = [{"type": "function", "function": {"name": "search_knowledge_base"}}]

    await provider.complete([ChatMessage(role="user", content="hi")], tools=tools)

    assert create.call_args.kwargs["tools"] == tools
    assert create.call_args.kwargs["tool_choice"] == "auto"


@pytest.mark.asyncio
async def test_complete_omits_tools_when_none_given(provider: GroqProvider):
    create = AsyncMock(return_value=make_chat_completion("hello"))
    provider._client.chat.completions.create = create

    await provider.complete([ChatMessage(role="user", content="hi")])

    assert "tools" not in create.call_args.kwargs
    assert "tool_choice" not in create.call_args.kwargs


@pytest.mark.asyncio
async def test_complete_parses_tool_calls_from_response(provider: GroqProvider):
    api_tool_call = make_api_tool_call("call_1", "search_knowledge_base", {"query": "refund policy"})
    provider._client.chat.completions.create = AsyncMock(
        return_value=make_chat_completion(None, finish_reason="tool_calls", tool_calls=[api_tool_call])
    )

    result = await provider.complete(
        [ChatMessage(role="user", content="hi")],
        tools=[{"type": "function", "function": {"name": "search_knowledge_base"}}],
    )

    assert result.finish_reason == "tool_calls"
    assert result.content == ""
    assert result.tool_calls == [
        ToolCall(id="call_1", name="search_knowledge_base", arguments={"query": "refund policy"})
    ]


@pytest.mark.asyncio
async def test_complete_serializes_assistant_tool_call_and_tool_result_messages(provider: GroqProvider):
    create = AsyncMock(return_value=make_chat_completion("final answer"))
    provider._client.chat.completions.create = create

    messages = [
        ChatMessage(role="user", content="How do I reset my password?"),
        ChatMessage(
            role="assistant",
            content=None,
            tool_calls=[ToolCall(id="call_1", name="search_knowledge_base", arguments={"query": "reset password"})],
        ),
        ChatMessage(role="tool", tool_call_id="call_1", content="Use the forgot password link."),
    ]

    await provider.complete(messages)

    sent_messages = create.call_args.kwargs["messages"]
    assert sent_messages[1] == {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "search_knowledge_base", "arguments": '{"query": "reset password"}'},
            }
        ],
    }
    assert sent_messages[2] == {
        "role": "tool",
        "content": "Use the forgot password link.",
        "tool_call_id": "call_1",
    }


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
