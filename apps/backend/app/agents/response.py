from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.prompts import RESPONSE_SYSTEM_PROMPT, build_context_block
from app.agents.schemas import SupportResponse
from app.llm.schemas import ChatMessage
from app.llm.service import LLMService
from app.retrieval.service import RetrievalService

FALLBACK_ANSWER = "I don't have enough information to answer that question."


class ResponseAgent:
    def __init__(self, llm_service: LLMService, retrieval_service: RetrievalService) -> None:
        self._llm_service = llm_service
        self._retrieval_service = retrieval_service

    async def respond(self, session: AsyncSession, question: str) -> SupportResponse:
        retrieval = await self._retrieval_service.search(session, question)
        if not retrieval.chunks:
            return SupportResponse(answer=FALLBACK_ANSWER, sources=[], grounded=False)

        context_block = build_context_block(retrieval.chunks)
        messages = [
            ChatMessage(role="system", content=RESPONSE_SYSTEM_PROMPT),
            ChatMessage(
                role="user",
                content=f"Context:\n{context_block}\n\nCustomer question: {question}",
            ),
        ]
        llm_response = await self._llm_service.complete(messages, temperature=0.2)
        sources = sorted({chunk.document for chunk in retrieval.chunks})
        return SupportResponse(answer=llm_response.content, sources=sources, grounded=True)
