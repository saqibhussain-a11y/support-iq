import json

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

import app.db.session as db_session_module
from app.agents.schemas import SupportResponse, TicketClassification
from app.db.models import TicketRecord
from app.db.session import get_db_session, session_scope
from app.hallucination.schemas import FaithfulnessVerdict
from app.main import app
from app.validation.schemas import EscalationLevel
from app.workflows.dependencies import get_support_workflow_service


class FakeWorkflowService:
    async def run(self, session, message: str) -> dict:
        return {
            "message": message,
            "classification": TicketClassification(
                category="billing", priority="high", sentiment="frustrated"
            ),
            "response": SupportResponse(
                answer="You're eligible for a refund.",
                sources=["doc.md"],
                grounded=True,
                top_rerank_score=5.9,
            ),
            "faithfulness": FaithfulnessVerdict(is_faithful=True, unsupported_claims=[]),
            "escalation": EscalationLevel.NONE,
            "escalation_reasons": [],
        }

    async def run_stream(self, session, message: str):
        result = await self.run(session, message)
        for stage in ("classify", "respond", "check_faithfulness", "validate"):
            update = {key: result[key] for key in result if key in FakeWorkflowService._STAGE_KEYS[stage]}
            yield stage, update

    _STAGE_KEYS = {
        "classify": {"classification"},
        "respond": {"response"},
        "check_faithfulness": {"faithfulness"},
        "validate": {"escalation", "escalation_reasons"},
    }


class FakeEscalatingWorkflowService(FakeWorkflowService):
    async def run(self, session, message: str) -> dict:
        result = await super().run(session, message)
        result["escalation"] = EscalationLevel.REVIEW
        result["escalation_reasons"] = ["retrieval confidence too low to trust the grounded answer"]
        return result


async def real_db_session():
    async with session_scope() as session:
        yield session


@pytest.fixture(autouse=True)
async def fresh_db_engine_per_test():
    db_session_module._engine = None
    db_session_module._session_factory = None
    yield
    async with session_scope() as session:
        await session.execute(delete(TicketRecord))
    if db_session_module._engine is not None:
        await db_session_module._engine.dispose()
    db_session_module._engine = None
    db_session_module._session_factory = None


@pytest.mark.asyncio
async def test_create_ticket_returns_classification_and_response():
    app.dependency_overrides[get_db_session] = real_db_session
    app.dependency_overrides[get_support_workflow_service] = lambda: FakeWorkflowService()

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/tickets", json={"message": "I was charged twice"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["classification"] == {"category": "billing", "priority": "high", "sentiment": "frustrated"}
    assert body["response"]["sources"] == ["doc.md"]
    assert body["response"]["grounded"] is True
    assert body["faithfulness"]["is_faithful"] is True
    assert body["escalation"] == "none"
    assert body["escalation_reasons"] == []
    assert body["status"] == "auto_resolved"
    assert body["id"]
    assert body["resolved_at"] is None


@pytest.mark.asyncio
async def test_stream_ticket_emits_stage_events_then_result():
    app.dependency_overrides[get_db_session] = real_db_session
    app.dependency_overrides[get_support_workflow_service] = lambda: FakeWorkflowService()

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            async with client.stream(
                "POST", "/api/tickets/stream", json={"message": "I was charged twice"}
            ) as response:
                assert response.status_code == 200
                body = await response.aread()
    finally:
        app.dependency_overrides.clear()

    events = [chunk for chunk in body.decode().split("\n\n") if chunk]
    stage_events = [e for e in events if e.startswith("event: stage")]
    result_events = [e for e in events if e.startswith("event: result")]

    assert [json.loads(e.split("data: ", 1)[1])["stage"] for e in stage_events] == [
        "classify",
        "respond",
        "check_faithfulness",
        "validate",
    ]
    assert len(result_events) == 1
    result_body = json.loads(result_events[0].split("data: ", 1)[1])
    assert result_body["classification"]["category"] == "billing"
    assert result_body["escalation"] == "none"
    assert result_body["status"] == "auto_resolved"


@pytest.mark.asyncio
async def test_escalated_ticket_is_listed_as_pending_review_then_resolvable():
    app.dependency_overrides[get_db_session] = real_db_session
    app.dependency_overrides[get_support_workflow_service] = lambda: FakeEscalatingWorkflowService()

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            create_response = await client.post("/api/tickets", json={"message": "unclear billing issue"})
            ticket_id = create_response.json()["id"]

            queue_response = await client.get("/api/tickets", params={"status": "pending_review"})
            assert any(ticket["id"] == ticket_id for ticket in queue_response.json())

            resolve_response = await client.post(
                f"/api/tickets/{ticket_id}/resolve", json={"notes": "Confirmed refund manually."}
            )
    finally:
        app.dependency_overrides.clear()

    assert create_response.json()["status"] == "pending_review"
    assert resolve_response.status_code == 200
    resolved_body = resolve_response.json()
    assert resolved_body["status"] == "resolved"
    assert resolved_body["resolution_notes"] == "Confirmed refund manually."
    assert resolved_body["resolved_at"] is not None


@pytest.mark.asyncio
async def test_resolving_unknown_ticket_returns_404():
    app.dependency_overrides[get_db_session] = real_db_session

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/tickets/00000000-0000-0000-0000-000000000000/resolve", json={"notes": None}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
