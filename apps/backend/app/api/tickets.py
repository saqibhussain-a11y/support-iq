from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.schemas import SupportResponse, TicketClassification
from app.db.session import get_db_session
from app.hallucination.schemas import FaithfulnessVerdict
from app.validation.schemas import EscalationLevel
from app.workflows.dependencies import get_support_workflow_service
from app.workflows.service import SupportWorkflowService

router = APIRouter(prefix="/api", tags=["tickets"])


class TicketRequest(BaseModel):
    message: str


class TicketResult(BaseModel):
    classification: TicketClassification
    response: SupportResponse
    faithfulness: FaithfulnessVerdict | None
    escalation: EscalationLevel
    escalation_reasons: list[str]


@router.post("/tickets", response_model=TicketResult)
async def create_ticket(
    request: TicketRequest,
    session: AsyncSession = Depends(get_db_session),
    workflow: SupportWorkflowService = Depends(get_support_workflow_service),
) -> TicketResult:
    result = await workflow.run(session, request.message)
    return TicketResult(
        classification=result["classification"],
        response=result["response"],
        faithfulness=result["faithfulness"],
        escalation=result["escalation"],
        escalation_reasons=result["escalation_reasons"],
    )
