import pytest

from app.agents.schemas import SupportResponse, TicketClassification
from app.validation.schemas import EscalationLevel
from app.workflows.service import SupportWorkflowService


class FakeClassifier:
    def __init__(self, classification: TicketClassification) -> None:
        self.classification = classification

    async def classify(self, message: str) -> TicketClassification:
        return self.classification


class FakeResponder:
    def __init__(self, top_rerank_score: float = 5.0) -> None:
        self.called = False
        self.top_rerank_score = top_rerank_score

    async def respond(self, session, question: str) -> SupportResponse:
        self.called = True
        return SupportResponse(
            answer="grounded answer",
            sources=["doc.md"],
            grounded=True,
            top_rerank_score=self.top_rerank_score,
        )


@pytest.mark.asyncio
async def test_workflow_routes_known_category_to_response_agent():
    classification = TicketClassification(category="billing", priority="high", sentiment="frustrated")
    responder = FakeResponder()
    service = SupportWorkflowService(classifier=FakeClassifier(classification), responder=responder)

    result = await service.run(session=object(), message="I was charged twice")

    assert responder.called is True
    assert result["classification"] == classification
    assert result["response"].answer == "grounded answer"
    assert result["escalation"] == EscalationLevel.NONE


@pytest.mark.asyncio
async def test_workflow_routes_other_category_to_clarify_and_skips_response_agent():
    classification = TicketClassification(category="other", priority="low", sentiment="neutral")
    responder = FakeResponder()
    service = SupportWorkflowService(classifier=FakeClassifier(classification), responder=responder)

    result = await service.run(session=object(), message="hello there")

    assert responder.called is False
    assert result["response"].grounded is False
    assert result["response"].sources == []
    assert result["escalation"] == EscalationLevel.NONE


@pytest.mark.asyncio
async def test_workflow_escalates_immediately_on_fraud_keyword_even_when_misclassified():
    classification = TicketClassification(category="other", priority="low", sentiment="neutral")
    responder = FakeResponder()
    service = SupportWorkflowService(classifier=FakeClassifier(classification), responder=responder)

    result = await service.run(session=object(), message="I think someone stole my card")

    assert result["escalation"] == EscalationLevel.IMMEDIATE
    assert result["escalation_reasons"]


@pytest.mark.asyncio
async def test_workflow_escalates_for_review_on_low_confidence_billing_dispute():
    classification = TicketClassification(category="billing", priority="high", sentiment="frustrated")
    responder = FakeResponder(top_rerank_score=-3.4)
    service = SupportWorkflowService(classifier=FakeClassifier(classification), responder=responder)

    result = await service.run(session=object(), message="I want a refund for my renewal")

    assert result["escalation"] == EscalationLevel.REVIEW
