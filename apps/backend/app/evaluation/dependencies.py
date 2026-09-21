from functools import lru_cache

from app.evaluation.judge import AnswerJudge
from app.evaluation.runner import EvaluationRunner
from app.llm.dependencies import get_llm_service
from app.workflows.dependencies import get_support_workflow_service


@lru_cache
def get_answer_judge() -> AnswerJudge:
    return AnswerJudge(llm_service=get_llm_service())


@lru_cache
def get_evaluation_runner() -> EvaluationRunner:
    return EvaluationRunner(workflow=get_support_workflow_service(), judge=get_answer_judge())
