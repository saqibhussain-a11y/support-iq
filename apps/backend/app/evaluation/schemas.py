from pydantic import BaseModel

from app.validation.schemas import EscalationLevel


class EvalCase(BaseModel):
    id: str
    message: str
    expected_category: str
    expected_escalation: EscalationLevel
    expected_sources: list[str]
    expected_facts: list[str]


class JudgeVerdict(BaseModel):
    score: float
    reasoning: str


class EvalCaseResult(BaseModel):
    case_id: str
    category_correct: bool
    retrieval_hit: bool
    escalation_correct: bool
    answer_score: float
    answer_reasoning: str
    passed: bool


class EvalReport(BaseModel):
    results: list[EvalCaseResult]
    category_accuracy: float
    retrieval_hit_rate: float
    escalation_accuracy: float
    mean_answer_score: float
    pass_rate: float
