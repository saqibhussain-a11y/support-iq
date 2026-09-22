import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from app.agents.schemas import SupportResponse, TicketClassification
from app.hallucination.schemas import FaithfulnessVerdict
from app.llm.schemas import TokenUsageBreakdown
from app.validation.schemas import EscalationLevel


class TicketStatus(str, Enum):
    AUTO_RESOLVED = "auto_resolved"
    PENDING_REVIEW = "pending_review"
    RESOLVED = "resolved"


class TicketRecordOut(BaseModel):
    id: uuid.UUID
    message: str
    classification: TicketClassification
    response: SupportResponse
    faithfulness: FaithfulnessVerdict | None
    escalation: EscalationLevel
    escalation_reasons: list[str]
    token_usage: TokenUsageBreakdown | None
    status: TicketStatus
    created_at: datetime
    resolved_at: datetime | None
    resolution_notes: str | None


class ResolveTicketRequest(BaseModel):
    notes: str | None = None
