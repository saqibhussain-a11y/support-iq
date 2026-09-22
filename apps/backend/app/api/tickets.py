import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
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


@router.post("/tickets/stream")
async def create_ticket_stream(
    request: TicketRequest,
    session: AsyncSession = Depends(get_db_session),
    workflow: SupportWorkflowService = Depends(get_support_workflow_service),
) -> StreamingResponse:
    async def event_source() -> AsyncIterator[str]:
        state: dict = {
            "classification": None,
            "response": None,
            "faithfulness": None,
            "escalation": None,
            "escalation_reasons": [],
        }
        async for stage, update in workflow.run_stream(session, request.message):
            state.update(update)
            yield f"event: stage\ndata: {json.dumps({'stage': stage})}\n\n"

        result = TicketResult(
            classification=state["classification"],
            response=state["response"],
            faithfulness=state["faithfulness"],
            escalation=state["escalation"],
            escalation_reasons=state["escalation_reasons"],
        )
        yield f"event: result\ndata: {result.model_dump_json()}\n\n"

    return StreamingResponse(event_source(), media_type="text/event-stream")
