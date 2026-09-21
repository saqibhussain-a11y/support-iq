import pytest

from app.agents.schemas import SupportResponse, TicketClassification
from app.workflows.service import SupportWorkflowService


class FakeClassifier:
    def __init__(self, classification: TicketClassification) -> None:
        self.classification = classification

    async def classify(self, message: str) -> TicketClassification:
        return self.classification


class FakeResponder:
    def __init__(self) -> None:
        self.called = False

    async def respond(self, session, question: str) -> SupportResponse:
        self.called = True
        return SupportResponse(answer="grounded answer", sources=["doc.md"], grounded=True)


@pytest.mark.asyncio
async def test_workflow_routes_known_category_to_response_agent():
    classification = TicketClassification(category="billing", priority="high", sentiment="frustrated")
    responder = FakeResponder()
    service = SupportWorkflowService(classifier=FakeClassifier(classification), responder=responder)

    result = await service.run(session=object(), message="I was charged twice")

    assert responder.called is True
    assert result["classification"] == classification
    assert result["response"].answer == "grounded answer"


@pytest.mark.asyncio
async def test_workflow_routes_other_category_to_clarify_and_skips_response_agent():
    classification = TicketClassification(category="other", priority="low", sentiment="neutral")
    responder = FakeResponder()
    service = SupportWorkflowService(classifier=FakeClassifier(classification), responder=responder)

    result = await service.run(session=object(), message="hello there")

    assert responder.called is False
    assert result["response"].grounded is False
    assert result["response"].sources == []
