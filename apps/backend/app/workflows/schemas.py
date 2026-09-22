from dataclasses import dataclass, field
from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.classifier import ClassifierAgent
from app.agents.response import ResponseAgent
from app.agents.schemas import SupportResponse, TicketClassification
from app.hallucination.checker import FaithfulnessChecker
from app.hallucination.schemas import FaithfulnessVerdict
from app.llm.schemas import TokenUsage, TokenUsageBreakdown
from app.validation.schemas import EscalationLevel


class TicketState(TypedDict):
    message: str
    classification: TicketClassification | None
    response: SupportResponse | None
    faithfulness: FaithfulnessVerdict | None
    escalation: EscalationLevel | None
    escalation_reasons: list[str]
    token_usage: TokenUsageBreakdown | None


@dataclass
class _StageUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def add(self, usage: TokenUsage) -> None:
        self.prompt_tokens += usage.prompt_tokens
        self.completion_tokens += usage.completion_tokens
        self.total_tokens += usage.total_tokens

    def to_schema(self) -> TokenUsage:
        return TokenUsage(
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            total_tokens=self.total_tokens,
        )


@dataclass
class TokenUsageTracker:
    classify: _StageUsage = field(default_factory=_StageUsage)
    respond: _StageUsage = field(default_factory=_StageUsage)
    faithfulness: _StageUsage = field(default_factory=_StageUsage)

    def to_breakdown(self) -> TokenUsageBreakdown:
        classify = self.classify.to_schema()
        respond = self.respond.to_schema()
        faithfulness = self.faithfulness.to_schema()
        total = TokenUsage(
            prompt_tokens=classify.prompt_tokens + respond.prompt_tokens + faithfulness.prompt_tokens,
            completion_tokens=(
                classify.completion_tokens + respond.completion_tokens + faithfulness.completion_tokens
            ),
            total_tokens=classify.total_tokens + respond.total_tokens + faithfulness.total_tokens,
        )
        return TokenUsageBreakdown(classify=classify, respond=respond, faithfulness=faithfulness, total=total)


@dataclass
class WorkflowContext:
    classifier: ClassifierAgent
    responder: ResponseAgent
    faithfulness_checker: FaithfulnessChecker
    session: AsyncSession
    token_usage: TokenUsageTracker = field(default_factory=TokenUsageTracker)
