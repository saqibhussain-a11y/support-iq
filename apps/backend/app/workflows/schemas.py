from dataclasses import dataclass
from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.classifier import ClassifierAgent
from app.agents.response import ResponseAgent
from app.agents.schemas import SupportResponse, TicketClassification
from app.validation.schemas import EscalationLevel


class TicketState(TypedDict):
    message: str
    classification: TicketClassification | None
    response: SupportResponse | None
    escalation: EscalationLevel | None
    escalation_reasons: list[str]


@dataclass
class WorkflowContext:
    classifier: ClassifierAgent
    responder: ResponseAgent
    session: AsyncSession
