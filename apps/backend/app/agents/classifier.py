from app.agents.prompts import CLASSIFIER_SYSTEM_PROMPT
from app.agents.schemas import TicketClassification
from app.llm.schemas import ChatMessage
from app.llm.service import LLMService


class ClassifierAgent:
    def __init__(self, llm_service: LLMService) -> None:
        self._llm_service = llm_service

    async def classify(self, message: str) -> TicketClassification:
        messages = [
            ChatMessage(role="system", content=CLASSIFIER_SYSTEM_PROMPT),
            ChatMessage(role="user", content=message),
        ]
        return await self._llm_service.complete_structured(messages, TicketClassification)
