from app.agents.schemas import SupportResponse, TicketClassification
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
) -> ValidationResult:
    if _mentions_immediate_escalation_keyword(message):
        return ValidationResult(
            escalation=EscalationLevel.IMMEDIATE,
            reasons=["message mentions fraud, unauthorized access, or a stolen payment method"],
        )

    if not response.answer.strip():
        return ValidationResult(escalation=EscalationLevel.REVIEW, reasons=["response answer was empty"])

    reasons: list[str] = []
    if response.grounded:
        low_confidence = (
            response.top_rerank_score is None
            or response.top_rerank_score < LOW_CONFIDENCE_RERANK_THRESHOLD
        )
        if low_confidence:
            reasons.append("retrieval confidence too low to trust the grounded answer")
        if classification.category == "billing" and classification.priority == "high" and low_confidence:
            reasons.append("high-priority billing dispute without a confident, documented match")

    if reasons:
        return ValidationResult(escalation=EscalationLevel.REVIEW, reasons=reasons)

    return ValidationResult(escalation=EscalationLevel.NONE, reasons=[])
