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
    def __init__(self, top_rerank_score: float = 5.0, emits_tool_call: bool = False) -> None:
        self.called = False
        self.top_rerank_score = top_rerank_score
        self.emits_tool_call = emits_tool_call

    async def respond(self, session, question: str, on_tool_call=None) -> SupportResponse:
        self.called = True
        if self.emits_tool_call and on_tool_call:
            on_tool_call({"phase": "start", "tool": "search_knowledge_base", "arguments": {"query": question}})
            on_tool_call({"phase": "end", "tool": "search_knowledge_base", "found": True, "sources": ["doc.md"]})
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


@pytest.mark.asyncio
async def test_run_stream_interleaves_tool_events_with_stage_events():
    classification = TicketClassification(category="billing", priority="low", sentiment="neutral")
    responder = FakeResponder(emits_tool_call=True)
    service = make_service(FakeClassifier(classification), responder)

    events = [event async for event in service.run_stream(session=object(), message="I was charged twice")]

    stage_names = [event["stage"] for event in events if event["kind"] == "stage"]
    tool_events = [event for event in events if event["kind"] == "tool"]

    assert stage_names == ["classify", "respond", "check_faithfulness", "validate"]
    assert tool_events == [
        {"kind": "tool", "phase": "start", "tool": "search_knowledge_base", "arguments": {"query": "I was charged twice"}},
        {"kind": "tool", "phase": "end", "tool": "search_knowledge_base", "found": True, "sources": ["doc.md"]},
    ]
    respond_index = stage_names.index("respond")
    tool_event_indices = [i for i, event in enumerate(events) if event["kind"] == "tool"]
    stage_event_indices = [i for i, event in enumerate(events) if event["kind"] == "stage"]
    assert min(tool_event_indices) > stage_event_indices[respond_index - 1]
    assert max(tool_event_indices) < stage_event_indices[respond_index]
