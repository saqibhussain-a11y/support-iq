import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.schemas import SupportResponse, TicketClassification
from app.db.models import TicketRecord
from app.hallucination.schemas import FaithfulnessVerdict
from app.llm.schemas import TokenUsageBreakdown
from app.tickets.schemas import TicketRecordOut, TicketStatus
from app.validation.schemas import EscalationLevel


def _status_for_escalation(escalation: EscalationLevel) -> TicketStatus:
    return TicketStatus.AUTO_RESOLVED if escalation == EscalationLevel.NONE else TicketStatus.PENDING_REVIEW


def _to_out(record: TicketRecord) -> TicketRecordOut:
    return TicketRecordOut(
        id=record.id,
        message=record.message,
        classification=TicketClassification(
            category=record.category, priority=record.priority, sentiment=record.sentiment
        ),
        response=SupportResponse(**record.response),
        faithfulness=FaithfulnessVerdict(**record.faithfulness) if record.faithfulness else None,
        escalation=EscalationLevel(record.escalation),
        escalation_reasons=record.escalation_reasons,
        token_usage=TokenUsageBreakdown(**record.token_usage) if record.token_usage else None,
        status=TicketStatus(record.status),
        created_at=record.created_at,
        resolved_at=record.resolved_at,
        resolution_notes=record.resolution_notes,
    )


async def save_ticket(
    session: AsyncSession,
    message: str,
    classification: TicketClassification,
    response: SupportResponse,
    faithfulness: FaithfulnessVerdict | None,
    escalation: EscalationLevel,
    escalation_reasons: list[str],
    token_usage: TokenUsageBreakdown | None = None,
) -> TicketRecordOut:
    record = TicketRecord(
        message=message,
        category=classification.category,
        priority=classification.priority,
        sentiment=classification.sentiment,
        response=response.model_dump(),
        faithfulness=faithfulness.model_dump() if faithfulness else None,
        escalation=escalation.value,
        escalation_reasons=escalation_reasons,
        token_usage=token_usage.model_dump() if token_usage else None,
        status=_status_for_escalation(escalation).value,
    )
    session.add(record)
    await session.flush()
    await session.refresh(record)
    return _to_out(record)


async def list_tickets(
    session: AsyncSession, status: TicketStatus | None = None, limit: int = 50
) -> list[TicketRecordOut]:
    query = select(TicketRecord).order_by(TicketRecord.created_at.desc()).limit(limit)
    if status is not None:
        query = query.where(TicketRecord.status == status.value)
    result = await session.execute(query)
    return [_to_out(record) for record in result.scalars().all()]


async def resolve_ticket(
    session: AsyncSession, ticket_id: uuid.UUID, notes: str | None
) -> TicketRecordOut | None:
    record = await session.get(TicketRecord, ticket_id)
    if record is None:
        return None
    record.status = TicketStatus.RESOLVED.value
    record.resolved_at = datetime.utcnow()
    record.resolution_notes = notes
    await session.flush()
    await session.refresh(record)
    return _to_out(record)
