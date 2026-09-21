from app.agents.schemas import SupportResponse, TicketClassification
from app.validation.rules import evaluate
from app.validation.schemas import EscalationLevel


def make_classification(category="billing", priority="high", sentiment="frustrated") -> TicketClassification:
    return TicketClassification(category=category, priority=priority, sentiment=sentiment)


def make_response(grounded=True, top_rerank_score=5.0, answer="answer") -> SupportResponse:
    return SupportResponse(
        answer=answer,
        sources=["doc.md"] if grounded else [],
        grounded=grounded,
        top_rerank_score=top_rerank_score,
    )


def test_confident_grounded_answer_resolves_automatically():
    result = evaluate("I was charged twice", make_classification(), make_response())

    assert result.escalation == EscalationLevel.NONE
    assert result.reasons == []


def test_fraud_keyword_escalates_immediately_regardless_of_classification():
    result = evaluate(
        "I think someone stole my card",
        make_classification(category="other", priority="low", sentiment="neutral"),
        make_response(grounded=False, top_rerank_score=None),
    )

    assert result.escalation == EscalationLevel.IMMEDIATE
    assert result.reasons


def test_unauthorized_access_keyword_escalates_immediately():
    result = evaluate(
        "There was unauthorized access to my account",
        make_classification(category="account", priority="medium", sentiment="angry"),
        make_response(),
    )

    assert result.escalation == EscalationLevel.IMMEDIATE


def test_low_confidence_billing_dispute_escalates_for_review():
    result = evaluate(
        "I want a refund for my renewal that I forgot to cancel",
        make_classification(category="billing", priority="high"),
        make_response(top_rerank_score=-3.4),
    )

    assert result.escalation == EscalationLevel.REVIEW
    assert any("confident" in reason for reason in result.reasons)


def test_low_confidence_non_billing_still_flags_review_but_not_immediate():
    result = evaluate(
        "What plan tiers are available?",
        make_classification(category="product", priority="low", sentiment="neutral"),
        make_response(top_rerank_score=-11.2),
    )

    assert result.escalation == EscalationLevel.REVIEW


def test_ungrounded_response_skips_confidence_check():
    result = evaluate(
        "hello there",
        make_classification(category="other", priority="low", sentiment="neutral"),
        make_response(grounded=False, top_rerank_score=None),
    )

    assert result.escalation == EscalationLevel.NONE
    assert result.reasons == []


def test_empty_answer_escalates_for_review():
    result = evaluate(
        "I was charged twice",
        make_classification(),
        make_response(answer="   "),
    )

    assert result.escalation == EscalationLevel.REVIEW
    assert "empty" in result.reasons[0]
