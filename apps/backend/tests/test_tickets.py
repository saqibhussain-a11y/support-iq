import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.agents.schemas import SupportResponse, TicketClassification
from app.db.session import get_db_session
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


async def fake_db_session():
    yield object()


@pytest.mark.asyncio
async def test_create_ticket_returns_classification_and_response():
    app.dependency_overrides[get_db_session] = fake_db_session
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


@pytest.mark.asyncio
async def test_stream_ticket_emits_stage_events_then_result():
    app.dependency_overrides[get_db_session] = fake_db_session
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
