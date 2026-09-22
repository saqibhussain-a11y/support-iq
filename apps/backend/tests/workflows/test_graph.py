import pytest

from app.agents.schemas import SupportResponse, TicketClassification
from app.hallucination.schemas import FaithfulnessVerdict
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
            context="the retrieved context",
        )


class FakeFaithfulnessChecker:
    def __init__(self, verdict: FaithfulnessVerdict | None = None) -> None:
        self.called = False
        self.verdict = verdict or FaithfulnessVerdict(is_faithful=True, unsupported_claims=[])

    async def check(self, answer: str, context: str) -> FaithfulnessVerdict:
        self.called = True
        return self.verdict


def make_service(classifier, responder, faithfulness_checker=None) -> SupportWorkflowService:
    return SupportWorkflowService(
        classifier=classifier,
        responder=responder,
        faithfulness_checker=faithfulness_checker or FakeFaithfulnessChecker(),
    )


@pytest.mark.asyncio
async def test_workflow_routes_known_category_to_response_agent():
    classification = TicketClassification(category="billing", priority="high", sentiment="frustrated")
    responder = FakeResponder()
    service = make_service(FakeClassifier(classification), responder)

    result = await service.run(session=object(), message="I was charged twice")

    assert responder.called is True
    assert result["classification"] == classification
    assert result["response"].answer == "grounded answer"
    assert result["escalation"] == EscalationLevel.NONE


@pytest.mark.asyncio
async def test_workflow_routes_other_category_to_clarify_and_skips_response_agent():
    classification = TicketClassification(category="other", priority="low", sentiment="neutral")
    responder = FakeResponder()
    checker = FakeFaithfulnessChecker()
    service = make_service(FakeClassifier(classification), responder, checker)

    result = await service.run(session=object(), message="hello there")

    assert responder.called is False
    assert checker.called is False
    assert result["response"].grounded is False
    assert result["response"].sources == []
    assert result["faithfulness"] is None
    assert result["escalation"] == EscalationLevel.REVIEW


@pytest.mark.asyncio
async def test_workflow_escalates_immediately_on_fraud_keyword_even_when_misclassified():
    classification = TicketClassification(category="other", priority="low", sentiment="neutral")
    responder = FakeResponder()
    service = make_service(FakeClassifier(classification), responder)

    result = await service.run(session=object(), message="I think someone stole my card")

    assert result["escalation"] == EscalationLevel.IMMEDIATE
    assert result["escalation_reasons"]


@pytest.mark.asyncio
async def test_workflow_escalates_for_review_on_low_confidence_billing_dispute():
    classification = TicketClassification(category="billing", priority="high", sentiment="frustrated")
    responder = FakeResponder(top_rerank_score=-3.4)
    service = make_service(FakeClassifier(classification), responder)

    result = await service.run(session=object(), message="I want a refund for my renewal")

    assert result["escalation"] == EscalationLevel.REVIEW


@pytest.mark.asyncio
async def test_workflow_checks_faithfulness_on_the_respond_path():
    classification = TicketClassification(category="billing", priority="low", sentiment="neutral")
    responder = FakeResponder()
    checker = FakeFaithfulnessChecker()
    service = make_service(FakeClassifier(classification), responder, checker)

    result = await service.run(session=object(), message="I was charged twice")

    assert checker.called is True
    assert result["faithfulness"].is_faithful is True


@pytest.mark.asyncio
async def test_workflow_escalates_for_review_when_answer_is_unfaithful():
    classification = TicketClassification(category="billing", priority="low", sentiment="neutral")
    responder = FakeResponder()
    checker = FakeFaithfulnessChecker(
        FaithfulnessVerdict(is_faithful=False, unsupported_claims=["invented a 60-day window"])
    )
    service = make_service(FakeClassifier(classification), responder, checker)

    result = await service.run(session=object(), message="I was charged twice")

    assert result["escalation"] == EscalationLevel.REVIEW
    assert "60-day window" in result["escalation_reasons"][0]
