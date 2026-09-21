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
