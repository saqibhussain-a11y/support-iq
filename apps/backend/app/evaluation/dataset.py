from app.evaluation.schemas import EvalCase
from app.validation.schemas import EscalationLevel

EVAL_CASES: list[EvalCase] = [
    EvalCase(
        id="duplicate_charge",
        message="I was charged twice for my subscription this month and I want a refund.",
        expected_category="billing",
        expected_escalation=EscalationLevel.NONE,
        expected_sources=["refund_policy.md", "duplicate_charges.md", "billing_faq.md"],
        expected_facts=[
            "duplicate charges are refundable in full",
            "refund requests must be made within 30 days",
        ],
    ),
    EvalCase(
        id="stolen_card",
        message="I think someone stole my card",
        expected_category="account",
        expected_escalation=EscalationLevel.IMMEDIATE,
        expected_sources=["account_security.md"],
        expected_facts=["this must be escalated immediately to the security team"],
    ),
    EvalCase(
        id="renewal_refund_forgot_to_cancel",
        message="I want to cancel my renewal and get a refund because I forgot to cancel in time",
        expected_category="billing",
        expected_escalation=EscalationLevel.REVIEW,
        expected_sources=["cancellation_policy.md", "refund_policy.md"],
        expected_facts=[
            "cancellation takes effect at the end of the billing period, not immediately",
            "a renewal refund requires less than 10 minutes of usage after renewal",
        ],
    ),
    EvalCase(
        id="password_reset",
        message="How do I reset my password?",
        expected_category="account",
        expected_escalation=EscalationLevel.NONE,
        expected_sources=["password_reset.md"],
        expected_facts=[
            "use the forgot password link on the login page",
            "the reset link expires after 1 hour",
        ],
    ),
    EvalCase(
        id="2fa_lockout_lost_device",
        message="I enabled 2FA and lost my device, I'm locked out of my account",
        expected_category="account",
        expected_escalation=EscalationLevel.REVIEW,
        expected_sources=["account_security.md"],
        expected_facts=["must be escalated to account security for identity verification"],
    ),
    EvalCase(
        id="plan_tiers",
        message="What plan tiers do you offer?",
        expected_category="product",
        expected_escalation=EscalationLevel.NONE,
        expected_sources=["subscription_policy.md"],
        expected_facts=[
            "there are Free, Pro, and Enterprise plan tiers",
            "downgrades take effect at the end of the billing cycle, not immediately",
        ],
    ),
    EvalCase(
        id="vague_greeting",
        message="hey",
        expected_category="other",
        expected_escalation=EscalationLevel.NONE,
        expected_sources=[],
        expected_facts=[],
    ),
    EvalCase(
        id="ambiguous_billing_charge",
        message="I don't think the charge on my account is right, something feels off",
        expected_category="billing",
        expected_escalation=EscalationLevel.REVIEW,
        expected_sources=["duplicate_charges.md"],
        expected_facts=[
            "check whether the charge is pending or completed",
            "confirmed duplicate charges are refunded in full",
        ],
    ),
]
