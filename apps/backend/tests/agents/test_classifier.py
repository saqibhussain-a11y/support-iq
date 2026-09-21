import pytest

from app.agents.classifier import ClassifierAgent
from app.agents.schemas import TicketClassification
from app.llm.provider import ModelProvider
from app.llm.schemas import ChatMessage, LLMResponse, TokenUsage
from app.llm.service import LLMService


class FakeProvider(ModelProvider):
    def __init__(self, response: LLMResponse) -> None:
        self.response = response
        self.received_messages: list[ChatMessage] | None = None

    async def complete(self, messages, *, temperature=0.7, top_p=1.0, json_mode=False):
        self.received_messages = messages
        return self.response

    async def stream(self, messages, *, temperature=0.7, top_p=1.0):
        yield self.response.content


def make_llm_response(content: str) -> LLMResponse:
    return LLMResponse(
        content=content,
        model="test-model",
        finish_reason="stop",
        usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
    )


@pytest.mark.asyncio
async def test_classify_parses_structured_response():
    provider = FakeProvider(
        make_llm_response('{"category": "billing", "priority": "high", "sentiment": "frustrated"}')
    )
    agent = ClassifierAgent(llm_service=LLMService(provider))

    result = await agent.classify("I was charged twice for my subscription.")

    assert result == TicketClassification(category="billing", priority="high", sentiment="frustrated")


@pytest.mark.asyncio
async def test_classify_sends_message_as_user_turn():
    provider = FakeProvider(
        make_llm_response('{"category": "other", "priority": "low", "sentiment": "neutral"}')
    )
    agent = ClassifierAgent(llm_service=LLMService(provider))

    await agent.classify("What are your store hours?")

    assert provider.received_messages[-1] == ChatMessage(
        role="user", content="What are your store hours?"
    )
