import pytest

from app.evaluation.judge import AnswerJudge
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
async def test_judge_parses_structured_verdict():
    provider = FakeProvider('{"score": 0.9, "reasoning": "covers the key facts"}')
    judge = AnswerJudge(llm_service=LLMService(provider))

    verdict = await judge.judge(
        question="Can I get a refund?",
        answer="Yes, duplicate charges are refundable within 30 days.",
        expected_facts=["duplicate charges are refundable", "30 day window"],
    )

    assert verdict.score == 0.9
    assert verdict.reasoning == "covers the key facts"


@pytest.mark.asyncio
async def test_judge_includes_question_answer_and_facts_in_prompt():
    provider = FakeProvider('{"score": 0.1, "reasoning": "missing facts"}')
    judge = AnswerJudge(llm_service=LLMService(provider))

    await judge.judge(
        question="How do I reset my password?",
        answer="Contact support.",
        expected_facts=["use the forgot password link"],
    )

    prompt = provider.received_messages[-1].content
    assert "How do I reset my password?" in prompt
    assert "Contact support." in prompt
    assert "use the forgot password link" in prompt
