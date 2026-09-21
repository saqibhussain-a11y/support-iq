import pytest

from app.hallucination.checker import FaithfulnessChecker
from app.llm.provider import ModelProvider
from app.llm.schemas import ChatMessage, LLMResponse, TokenUsage
from app.llm.service import LLMService


class FakeProvider(ModelProvider):
    def __init__(self, content: str) -> None:
        self.content = content
        self.received_messages: list[ChatMessage] | None = None

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


@pytest.mark.asyncio
async def test_check_parses_faithful_verdict():
    provider = FakeProvider('{"is_faithful": true, "unsupported_claims": []}')
    checker = FaithfulnessChecker(llm_service=LLMService(provider))

    verdict = await checker.check(
        answer="Duplicate charges are refundable within 30 days.",
        context="Confirmed duplicate charges are always refundable in full within 30 days.",
    )

    assert verdict.is_faithful is True
    assert verdict.unsupported_claims == []


@pytest.mark.asyncio
async def test_check_parses_unfaithful_verdict_with_claims():
    provider = FakeProvider(
        '{"is_faithful": false, "unsupported_claims": ["a 60-day refund window"]}'
    )
    checker = FaithfulnessChecker(llm_service=LLMService(provider))

    verdict = await checker.check(
        answer="You have 60 days to request a refund.",
        context="Refunds may be requested within 30 days of the original charge date.",
    )

    assert verdict.is_faithful is False
    assert verdict.unsupported_claims == ["a 60-day refund window"]


@pytest.mark.asyncio
async def test_check_includes_context_and_answer_in_prompt():
    provider = FakeProvider('{"is_faithful": true, "unsupported_claims": []}')
    checker = FaithfulnessChecker(llm_service=LLMService(provider))

    await checker.check(answer="the answer text", context="the context text")

    prompt = provider.received_messages[-1].content
    assert "the answer text" in prompt
    assert "the context text" in prompt
