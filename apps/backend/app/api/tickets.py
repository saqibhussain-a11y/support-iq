import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session, session_scope
from app.tickets.repository import list_tickets, resolve_ticket, save_ticket
from app.tickets.schemas import ResolveTicketRequest, TicketRecordOut, TicketStatus
from app.workflows.dependencies import get_support_workflow_service
from app.workflows.service import SupportWorkflowService

router = APIRouter(prefix="/api", tags=["tickets"])


class TicketRequest(BaseModel):
    message: str


@router.post("/tickets", response_model=TicketRecordOut)
async def create_ticket(
    request: TicketRequest,
    session: AsyncSession = Depends(get_db_session),
    workflow: SupportWorkflowService = Depends(get_support_workflow_service),
) -> TicketRecordOut:
    result = await workflow.run(session, request.message)
    return await save_ticket(
        session,
        message=request.message,
        classification=result["classification"],
        response=result["response"],
        faithfulness=result["faithfulness"],
        escalation=result["escalation"],
        escalation_reasons=result["escalation_reasons"],
    )


@router.post("/tickets/stream")
async def create_ticket_stream(
    request: TicketRequest,
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
        async with session_scope() as session:
            async for stage, update in workflow.run_stream(session, request.message):
                state.update(update)
                yield f"event: stage\ndata: {json.dumps({'stage': stage})}\n\n"

            record = await save_ticket(
                session,
                message=request.message,
                classification=state["classification"],
                response=state["response"],
                faithfulness=state["faithfulness"],
                escalation=state["escalation"],
                escalation_reasons=state["escalation_reasons"],
            )
        yield f"event: result\ndata: {record.model_dump_json()}\n\n"

    return StreamingResponse(event_source(), media_type="text/event-stream")


@router.get("/tickets", response_model=list[TicketRecordOut])
async def get_tickets(
    status: TicketStatus | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> list[TicketRecordOut]:
    return await list_tickets(session, status=status)


@router.post("/tickets/{ticket_id}/resolve", response_model=TicketRecordOut)
async def resolve_ticket_route(
    ticket_id: uuid.UUID,
    request: ResolveTicketRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TicketRecordOut:
    record = await resolve_ticket(session, ticket_id, request.notes)
    if record is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return record
