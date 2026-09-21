from enum import Enum

from pydantic import BaseModel


class EscalationLevel(str, Enum):
    NONE = "none"
    REVIEW = "review"
    IMMEDIATE = "immediate"


class ValidationResult(BaseModel):
    escalation: EscalationLevel
    reasons: list[str]
