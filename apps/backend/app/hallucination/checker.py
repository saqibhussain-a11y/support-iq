from app.hallucination.prompts import FAITHFULNESS_SYSTEM_PROMPT
from app.hallucination.schemas import FaithfulnessVerdict
from app.llm.schemas import ChatMessage
from app.llm.service import LLMService


class FaithfulnessChecker:
    def __init__(self, llm_service: LLMService) -> None:
        self._llm_service = llm_service

    async def check(self, answer: str, context: str) -> FaithfulnessVerdict:
        messages = [
            ChatMessage(role="system", content=FAITHFULNESS_SYSTEM_PROMPT),
            ChatMessage(
                role="user",
                content=f"Context:\n{context}\n\nAnswer:\n{answer}",
            ),
        ]
        return await self._llm_service.complete_structured(messages, FaithfulnessVerdict, temperature=0.0)
