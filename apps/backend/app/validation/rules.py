from app.agents.schemas import SupportResponse, TicketClassification
from app.hallucination.schemas import FaithfulnessVerdict
from app.validation.schemas import EscalationLevel, ValidationResult

IMMEDIATE_ESCALATION_KEYWORDS = (
    "stole",
    "stolen",
    "fraud",
    "fraudulent",
    "unauthorized",
    "hacked",
    "hack",
    "compromised",
)

LOW_CONFIDENCE_RERANK_THRESHOLD = 0.0


def _mentions_immediate_escalation_keyword(message: str) -> bool:
    lowered = message.lower()
    return any(keyword in lowered for keyword in IMMEDIATE_ESCALATION_KEYWORDS)


def evaluate(
    message: str,
    classification: TicketClassification,
    response: SupportResponse,
    faithfulness: FaithfulnessVerdict | None = None,
) -> ValidationResult:
    if _mentions_immediate_escalation_keyword(message):
        return ValidationResult(
            escalation=EscalationLevel.IMMEDIATE,
            reasons=["message mentions fraud, unauthorized access, or a stolen payment method"],
        )

    if not response.answer.strip():
        return ValidationResult(escalation=EscalationLevel.REVIEW, reasons=["response answer was empty"])

    reasons: list[str] = []
    if faithfulness is not None and not faithfulness.is_faithful:
        claims = "; ".join(faithfulness.unsupported_claims)
        reasons.append(f"answer contains claims not supported by the retrieved context: {claims}")

    if response.grounded:
        low_confidence = (
            response.top_rerank_score is None
            or response.top_rerank_score < LOW_CONFIDENCE_RERANK_THRESHOLD
        )
        if low_confidence:
            reasons.append("retrieval confidence too low to trust the grounded answer")
        if classification.category == "billing" and classification.priority == "high" and low_confidence:
            reasons.append("high-priority billing dispute without a confident, documented match")
    else:
        reasons.append("no documented policy matched this request; needs human triage")

    if reasons:
        return ValidationResult(escalation=EscalationLevel.REVIEW, reasons=reasons)

    return ValidationResult(escalation=EscalationLevel.NONE, reasons=[])
