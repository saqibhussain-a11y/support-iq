from dataclasses import dataclass
from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.classifier import ClassifierAgent
from app.agents.response import ResponseAgent
from app.agents.schemas import SupportResponse, TicketClassification


class TicketState(TypedDict):
    message: str
    classification: TicketClassification | None
    response: SupportResponse | None


@dataclass
class WorkflowContext:
    classifier: ClassifierAgent
    responder: ResponseAgent
    session: AsyncSession
