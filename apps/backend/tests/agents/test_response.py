from unittest.mock import AsyncMock

import pytest

from app.agents.response import ResponseAgent
from app.llm.provider import ModelProvider
from app.llm.schemas import LLMResponse, TokenUsage
from app.llm.service import LLMService
from app.retrieval.schemas import RetrievalResult, RetrievedChunk


class FakeProvider(ModelProvider):
    def __init__(self, content: str) -> None:
        self.content = content
        self.received_messages = None

    async def complete(self, messages, *, temperature=0.7, top_p=1.0, json_mode=False):
        self.received_messages = messages
        return LLMResponse(
            content=self.content,
            model="test-model",
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        )

    async def stream(self, messages, *, temperature=0.7, top_p=1.0):
        yield self.content


def make_chunk(document: str, content: str, rerank_score: float = 1.0) -> RetrievedChunk:
    return RetrievedChunk(
        document=document,
        category="billing",
        chunk_index=0,
        content=content,
        fused_score=1.0,
        rerank_score=rerank_score,
    )


@pytest.mark.asyncio
async def test_respond_grounds_answer_in_retrieved_context():
    provider = FakeProvider("Duplicate charges are refundable within 30 days.")
    retrieval_service = AsyncMock()
    retrieval_service.search.return_value = RetrievalResult(
        query="q",
        chunks=[make_chunk("refund_policy.md", "Duplicate charges are always refundable.")],
    )
    agent = ResponseAgent(llm_service=LLMService(provider), retrieval_service=retrieval_service)

    result = await agent.respond(session=object(), question="Can I get a refund for a duplicate charge?")

    assert result.answer == "Duplicate charges are refundable within 30 days."
    assert result.sources == ["refund_policy.md"]
    assert result.grounded is True
    assert result.top_rerank_score == 1.0
    assert "Duplicate charges are always refundable." in provider.received_messages[-1].content


@pytest.mark.asyncio
async def test_respond_returns_fallback_when_no_chunks_found():
    provider = FakeProvider("should not be used")
    retrieval_service = AsyncMock()
    retrieval_service.search.return_value = RetrievalResult(query="q", chunks=[])
    agent = ResponseAgent(llm_service=LLMService(provider), retrieval_service=retrieval_service)

    result = await agent.respond(session=object(), question="What is the meaning of life?")

    assert result.grounded is False
    assert result.sources == []
    assert result.top_rerank_score is None
    assert provider.received_messages is None


@pytest.mark.asyncio
async def test_respond_deduplicates_and_sorts_sources():
    provider = FakeProvider("answer")
    retrieval_service = AsyncMock()
    retrieval_service.search.return_value = RetrievalResult(
        query="q",
        chunks=[
            make_chunk("refund_policy.md", "chunk a"),
            make_chunk("billing_faq.md", "chunk b"),
            make_chunk("refund_policy.md", "chunk c"),
        ],
    )
    agent = ResponseAgent(llm_service=LLMService(provider), retrieval_service=retrieval_service)

    result = await agent.respond(session=object(), question="q")

    assert result.sources == ["billing_faq.md", "refund_policy.md"]


@pytest.mark.asyncio
async def test_respond_sets_top_rerank_score_to_the_best_candidate():
    provider = FakeProvider("answer")
    retrieval_service = AsyncMock()
    retrieval_service.search.return_value = RetrievalResult(
        query="q",
        chunks=[
            make_chunk("a.md", "chunk a", rerank_score=-3.4),
            make_chunk("b.md", "chunk b", rerank_score=5.9),
            make_chunk("c.md", "chunk c", rerank_score=2.3),
        ],
    )
    agent = ResponseAgent(llm_service=LLMService(provider), retrieval_service=retrieval_service)

    result = await agent.respond(session=object(), question="q")

    assert result.top_rerank_score == 5.9
