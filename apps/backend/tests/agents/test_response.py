from unittest.mock import AsyncMock

import pytest

from app.agents.response import MAX_TOOL_ROUNDS, ResponseAgent
from app.agents.tools import TOOL_SPECS
from app.llm.provider import ModelProvider
from app.llm.schemas import LLMResponse, TokenUsage, ToolCall
from app.llm.service import LLMService
from app.retrieval.schemas import RetrievalResult, RetrievedChunk


class ScriptedProvider(ModelProvider):
    def __init__(self, responses: list[LLMResponse]) -> None:
        self._responses = list(responses)
        self.received_message_histories: list[list] = []
        self.received_tools: list[list[dict] | None] = []

    async def complete(self, messages, *, temperature=0.7, top_p=1.0, json_mode=False, tools=None):
        self.received_message_histories.append(list(messages))
        self.received_tools.append(tools)
        return self._responses.pop(0)

    async def stream(self, messages, *, temperature=0.7, top_p=1.0):
        yield ""


def make_chunk(document: str, content: str, rerank_score: float = 1.0) -> RetrievedChunk:
    return RetrievedChunk(
        document=document,
        category="billing",
        chunk_index=0,
        content=content,
        fused_score=1.0,
        rerank_score=rerank_score,
    )


def usage() -> TokenUsage:
    return TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2)


def tool_call_response(name: str, arguments: dict, call_id: str = "call_1") -> LLMResponse:
    return LLMResponse(
        content="",
        model="test-model",
        finish_reason="tool_calls",
        usage=usage(),
        tool_calls=[ToolCall(id=call_id, name=name, arguments=arguments)],
    )


def multi_tool_call_response(calls: list[tuple[str, dict, str]]) -> LLMResponse:
    return LLMResponse(
        content="",
        model="test-model",
        finish_reason="tool_calls",
        usage=usage(),
        tool_calls=[ToolCall(id=call_id, name=name, arguments=args) for name, args, call_id in calls],
    )


def final_response(text: str) -> LLMResponse:
    return LLMResponse(content=text, model="test-model", finish_reason="stop", usage=usage(), tool_calls=None)


@pytest.mark.asyncio
async def test_respond_calls_search_tool_then_answers():
    provider = ScriptedProvider(
        [
            tool_call_response("search_knowledge_base", {"query": "duplicate charge refund"}),
            final_response("Duplicate charges are refundable within 30 days."),
        ]
    )
    retrieval_service = AsyncMock()
    retrieval_service.search.return_value = RetrievalResult(
        query="q", chunks=[make_chunk("refund_policy.md", "Duplicate charges are always refundable.")]
    )
    agent = ResponseAgent(llm_service=LLMService(provider), retrieval_service=retrieval_service)

    result = await agent.respond(session=object(), question="Can I get a refund for a duplicate charge?")

    assert result.answer == "Duplicate charges are refundable within 30 days."
    assert result.sources == ["refund_policy.md"]
    assert result.grounded is True
    assert result.top_rerank_score == 1.0
    assert "Duplicate charges are always refundable." in result.context
    retrieval_service.search.assert_awaited_once()
    assert retrieval_service.search.call_args.args[1] == "duplicate charge refund"


@pytest.mark.asyncio
async def test_respond_uses_get_full_document_tool(monkeypatch):
    provider = ScriptedProvider(
        [
            tool_call_response("get_full_document", {"document_name": "refund_policy.md"}),
            final_response("Here is the refund policy in full."),
        ]
    )
    retrieval_service = AsyncMock()

    async def fake_fetch_full_document(session, document_name):
        assert document_name == "refund_policy.md"
        return "Full refund policy text."

    monkeypatch.setattr("app.agents.response.fetch_full_document", fake_fetch_full_document)

    agent = ResponseAgent(llm_service=LLMService(provider), retrieval_service=retrieval_service)
    result = await agent.respond(session=object(), question="What's the full refund policy?")

    assert result.answer == "Here is the refund policy in full."
    assert result.sources == ["refund_policy.md"]
    assert result.grounded is True
    assert result.top_rerank_score == 10.0
    retrieval_service.search.assert_not_called()


@pytest.mark.asyncio
async def test_respond_answers_directly_when_model_skips_tools():
    provider = ScriptedProvider([final_response("Hi, how can I help?")])
    retrieval_service = AsyncMock()
    agent = ResponseAgent(llm_service=LLMService(provider), retrieval_service=retrieval_service)

    result = await agent.respond(session=object(), question="hello")

    assert result.grounded is False
    assert result.answer == "I don't have enough information to answer that question."
    assert result.sources == []
    retrieval_service.search.assert_not_called()


@pytest.mark.asyncio
async def test_respond_returns_fallback_when_search_finds_nothing():
    provider = ScriptedProvider(
        [
            tool_call_response("search_knowledge_base", {"query": "meaning of life"}),
            final_response("I couldn't find anything about that."),
        ]
    )
    retrieval_service = AsyncMock()
    retrieval_service.search.return_value = RetrievalResult(query="q", chunks=[])
    agent = ResponseAgent(llm_service=LLMService(provider), retrieval_service=retrieval_service)

    result = await agent.respond(session=object(), question="What is the meaning of life?")

    assert result.grounded is False
    assert result.sources == []
    assert result.answer == "I don't have enough information to answer that question."


@pytest.mark.asyncio
async def test_respond_executes_multiple_tool_calls_in_one_round(monkeypatch):
    provider = ScriptedProvider(
        [
            multi_tool_call_response(
                [
                    ("search_knowledge_base", {"query": "refund window"}, "call_1"),
                    ("get_full_document", {"document_name": "billing_faq.md"}, "call_2"),
                ]
            ),
            final_response("Combined answer."),
        ]
    )
    retrieval_service = AsyncMock()
    retrieval_service.search.return_value = RetrievalResult(
        query="q", chunks=[make_chunk("refund_policy.md", "chunk", rerank_score=3.0)]
    )

    async def fake_fetch_full_document(session, document_name):
        return "Billing FAQ text."

    monkeypatch.setattr("app.agents.response.fetch_full_document", fake_fetch_full_document)
    agent = ResponseAgent(llm_service=LLMService(provider), retrieval_service=retrieval_service)

    result = await agent.respond(session=object(), question="q")

    assert result.sources == ["billing_faq.md", "refund_policy.md"]
    assert result.top_rerank_score == 10.0


@pytest.mark.asyncio
async def test_respond_answers_cleanly_when_model_stops_calling_tools_before_the_cap():
    responses = [
        tool_call_response("search_knowledge_base", {"query": f"q{i}"}, call_id=f"call_{i}")
        for i in range(MAX_TOOL_ROUNDS - 1)
    ] + [final_response("Final answer.")]
    provider = ScriptedProvider(responses)
    retrieval_service = AsyncMock()
    retrieval_service.search.return_value = RetrievalResult(
        query="q", chunks=[make_chunk("doc.md", "chunk", rerank_score=2.0)]
    )
    agent = ResponseAgent(llm_service=LLMService(provider), retrieval_service=retrieval_service)

    result = await agent.respond(session=object(), question="q")

    assert result.answer == "Final answer."
    assert all(tools == TOOL_SPECS for tools in provider.received_tools)


@pytest.mark.asyncio
async def test_respond_falls_back_when_model_keeps_calling_tools_past_the_round_cap():
    responses = [
        tool_call_response("search_knowledge_base", {"query": f"q{i}"}, call_id=f"call_{i}")
        for i in range(MAX_TOOL_ROUNDS)
    ]
    provider = ScriptedProvider(responses)
    retrieval_service = AsyncMock()
    retrieval_service.search.return_value = RetrievalResult(
        query="q", chunks=[make_chunk("doc.md", "chunk", rerank_score=2.0)]
    )
    agent = ResponseAgent(llm_service=LLMService(provider), retrieval_service=retrieval_service)

    result = await agent.respond(session=object(), question="q")

    assert result.answer == "I don't have enough information to answer that question."
    assert result.grounded is True
    assert result.sources == ["doc.md"]
    assert len(provider.received_message_histories) == MAX_TOOL_ROUNDS


@pytest.mark.asyncio
async def test_respond_deduplicates_and_sorts_sources_across_searches():
    provider = ScriptedProvider(
        [
            tool_call_response("search_knowledge_base", {"query": "a"}, call_id="call_1"),
            tool_call_response("search_knowledge_base", {"query": "b"}, call_id="call_2"),
            final_response("answer"),
        ]
    )
    retrieval_service = AsyncMock()
    retrieval_service.search.side_effect = [
        RetrievalResult(query="a", chunks=[make_chunk("refund_policy.md", "chunk a")]),
        RetrievalResult(
            query="b",
            chunks=[make_chunk("billing_faq.md", "chunk b"), make_chunk("refund_policy.md", "chunk c")],
        ),
    ]
    agent = ResponseAgent(llm_service=LLMService(provider), retrieval_service=retrieval_service)

    result = await agent.respond(session=object(), question="q")

    assert result.sources == ["billing_faq.md", "refund_policy.md"]


@pytest.mark.asyncio
async def test_respond_notifies_on_usage_listener_once_per_completion_call():
    provider = ScriptedProvider(
        [
            tool_call_response("search_knowledge_base", {"query": "refund window"}),
            final_response("answer"),
        ]
    )
    retrieval_service = AsyncMock()
    retrieval_service.search.return_value = RetrievalResult(
        query="q", chunks=[make_chunk("refund_policy.md", "chunk", rerank_score=4.0)]
    )
    agent = ResponseAgent(llm_service=LLMService(provider), retrieval_service=retrieval_service)
    usages: list[TokenUsage] = []

    await agent.respond(session=object(), question="q", on_usage=usages.append)

    assert usages == [usage(), usage()]


@pytest.mark.asyncio
async def test_respond_notifies_on_tool_call_listener_with_start_and_end_events():
    provider = ScriptedProvider(
        [
            tool_call_response("search_knowledge_base", {"query": "refund window"}),
            final_response("answer"),
        ]
    )
    retrieval_service = AsyncMock()
    retrieval_service.search.return_value = RetrievalResult(
        query="q", chunks=[make_chunk("refund_policy.md", "chunk", rerank_score=4.0)]
    )
    agent = ResponseAgent(llm_service=LLMService(provider), retrieval_service=retrieval_service)
    events: list[dict] = []

    await agent.respond(session=object(), question="q", on_tool_call=events.append)

    assert events == [
        {"phase": "start", "tool": "search_knowledge_base", "arguments": {"query": "refund window"}},
        {"phase": "end", "tool": "search_knowledge_base", "found": True, "sources": ["refund_policy.md"]},
    ]


@pytest.mark.asyncio
async def test_respond_notifies_on_tool_call_listener_when_nothing_is_found(monkeypatch):
    provider = ScriptedProvider(
        [
            tool_call_response("get_full_document", {"document_name": "missing.md"}),
            final_response("I don't have enough information to answer that question."),
        ]
    )
    retrieval_service = AsyncMock()

    async def fake_fetch_full_document(session, document_name):
        return None

    monkeypatch.setattr("app.agents.response.fetch_full_document", fake_fetch_full_document)
    agent = ResponseAgent(llm_service=LLMService(provider), retrieval_service=retrieval_service)
    events: list[dict] = []

    await agent.respond(session=object(), question="q", on_tool_call=events.append)

    assert events[-1] == {"phase": "end", "tool": "get_full_document", "found": False, "sources": []}


@pytest.mark.asyncio
async def test_respond_sets_top_rerank_score_to_the_best_candidate_across_searches():
    provider = ScriptedProvider(
        [
            tool_call_response("search_knowledge_base", {"query": "a"}, call_id="call_1"),
            tool_call_response("search_knowledge_base", {"query": "b"}, call_id="call_2"),
            final_response("answer"),
        ]
    )
    retrieval_service = AsyncMock()
    retrieval_service.search.side_effect = [
        RetrievalResult(query="a", chunks=[make_chunk("a.md", "chunk a", rerank_score=-3.4)]),
        RetrievalResult(query="b", chunks=[make_chunk("b.md", "chunk b", rerank_score=5.9)]),
    ]
    agent = ResponseAgent(llm_service=LLMService(provider), retrieval_service=retrieval_service)

    result = await agent.respond(session=object(), question="q")

    assert result.top_rerank_score == 5.9
