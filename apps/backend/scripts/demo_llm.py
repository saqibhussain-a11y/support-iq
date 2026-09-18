import asyncio

from pydantic import BaseModel

from app.llm.dependencies import get_llm_service
from app.llm.schemas import ChatMessage

DEMO_SYSTEM_PROMPT = (
    "You are a customer support ticket classifier for a flooring e-commerce company. "
    "Classify the customer message and respond with strict JSON only, matching this shape: "
    '{"category": "billing|shipping|product|account|other", '
    '"priority": "low|medium|high", '
    '"sentiment": "positive|neutral|frustrated|angry"}'
)


class DemoClassification(BaseModel):
    category: str
    priority: str
    sentiment: str


async def main() -> None:
    service = get_llm_service()
    messages = [
        ChatMessage(role="system", content=DEMO_SYSTEM_PROMPT),
        ChatMessage(
            role="user",
            content="I was charged twice for my Pro subscription this month and I want a refund.",
        ),
    ]
    result = await service.complete_structured(messages, DemoClassification)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
