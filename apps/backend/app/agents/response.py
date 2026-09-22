from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.prompts import AGENTIC_RESPONSE_SYSTEM_PROMPT
from app.agents.schemas import SupportResponse
from app.agents.tools import TOOL_SPECS
from app.llm.schemas import ChatMessage, ToolCall
from app.llm.service import LLMService
from app.observability.tracing import get_tracer
from app.retrieval.documents import fetch_full_document
from app.retrieval.service import RetrievalService

FALLBACK_ANSWER = "I don't have enough information to answer that question."
MAX_TOOL_ROUNDS = 3
EXACT_DOCUMENT_MATCH_SCORE = 10.0


@dataclass
class _ToolOutcome:
    content: str
    sources: set[str] = field(default_factory=set)
    rerank_score: float | None = None


class ResponseAgent:
    def __init__(self, llm_service: LLMService, retrieval_service: RetrievalService) -> None:
        self._llm_service = llm_service
        self._retrieval_service = retrieval_service

    async def respond(self, session: AsyncSession, question: str) -> SupportResponse:
        messages = [
            ChatMessage(role="system", content=AGENTIC_RESPONSE_SYSTEM_PROMPT),
            ChatMessage(role="user", content=question),
        ]
        sources: set[str] = set()
        context_parts: list[str] = []
        top_rerank_score: float | None = None

        for round_index in range(MAX_TOOL_ROUNDS):
            llm_response = await self._llm_service.complete(messages, temperature=0.2, tools=TOOL_SPECS)

            if not llm_response.tool_calls:
                if not sources:
                    return SupportResponse(answer=FALLBACK_ANSWER, sources=[], grounded=False)
                return SupportResponse(
                    answer=llm_response.content,
                    sources=sorted(sources),
                    grounded=True,
                    top_rerank_score=top_rerank_score,
                    context="\n\n".join(context_parts),
                )

            if round_index == MAX_TOOL_ROUNDS - 1:
                # Hit the round cap and the model still wants to call tools. Asking Groq for a
                # forced tools=None reply here is unreliable - gpt-oss can still emit a tool-call
                # shaped generation and the API hard-errors instead of degrading gracefully. Stop
                # acting on further tool calls and fall back with whatever grounding we already have.
                break

            messages.append(
                ChatMessage(
                    role="assistant", content=llm_response.content or None, tool_calls=llm_response.tool_calls
                )
            )
            for tool_call in llm_response.tool_calls:
                outcome = await self._execute_tool(session, tool_call)
                sources |= outcome.sources
                if outcome.content:
                    context_parts.append(outcome.content)
                if outcome.rerank_score is not None:
                    top_rerank_score = (
                        outcome.rerank_score if top_rerank_score is None else max(top_rerank_score, outcome.rerank_score)
                    )
                messages.append(ChatMessage(role="tool", tool_call_id=tool_call.id, content=outcome.content))

        if not sources:
            return SupportResponse(answer=FALLBACK_ANSWER, sources=[], grounded=False)
        return SupportResponse(
            answer=FALLBACK_ANSWER,
            sources=sorted(sources),
            grounded=True,
            top_rerank_score=top_rerank_score,
            context="\n\n".join(context_parts),
        )

    async def _execute_tool(self, session: AsyncSession, tool_call: ToolCall) -> _ToolOutcome:
        with get_tracer().start_as_current_span("agent.tool_call") as span:
            span.set_attribute("tool.name", tool_call.name)
            outcome = await self._run_tool(session, tool_call)
            span.set_attribute("tool.source_count", len(outcome.sources))
            return outcome

    async def _run_tool(self, session: AsyncSession, tool_call: ToolCall) -> _ToolOutcome:
        if tool_call.name == "search_knowledge_base":
            query = str(tool_call.arguments.get("query", ""))
            retrieval = await self._retrieval_service.search(session, query)
            if not retrieval.chunks:
                return _ToolOutcome(content="No matching documents found.")
            content = "\n\n".join(f"[Source: {chunk.document}]\n{chunk.content}" for chunk in retrieval.chunks)
            return _ToolOutcome(
                content=content,
                sources={chunk.document for chunk in retrieval.chunks},
                rerank_score=max(chunk.rerank_score for chunk in retrieval.chunks),
            )

        if tool_call.name == "get_full_document":
            document_name = str(tool_call.arguments.get("document_name", ""))
            document_text = await fetch_full_document(session, document_name)
            if document_text is None:
                return _ToolOutcome(content=f"No document named '{document_name}' was found.")
            return _ToolOutcome(
                content=f"[Source: {document_name}]\n{document_text}",
                sources={document_name},
                rerank_score=EXACT_DOCUMENT_MATCH_SCORE,
            )

        return _ToolOutcome(content=f"Unknown tool '{tool_call.name}'.")
