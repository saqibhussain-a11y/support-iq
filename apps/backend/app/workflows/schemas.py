from dataclasses import dataclass
from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.classifier import ClassifierAgent
from app.agents.response import ResponseAgent
from app.agents.schemas import SupportResponse, TicketClassification
from app.hallucination.checker import FaithfulnessChecker
from app.hallucination.schemas import FaithfulnessVerdict
from app.validation.schemas import EscalationLevel


class TicketState(TypedDict):
    message: str
    classification: TicketClassification | None
    response: SupportResponse | None
    faithfulness: FaithfulnessVerdict | None
    escalation: EscalationLevel | None
    escalation_reasons: list[str]


@dataclass
class WorkflowContext:
    classifier: ClassifierAgent
    responder: ResponseAgent
    faithfulness_checker: FaithfulnessChecker
    session: AsyncSession
