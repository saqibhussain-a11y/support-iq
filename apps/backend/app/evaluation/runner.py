from sqlalchemy.ext.asyncio import AsyncSession

from app.evaluation.judge import AnswerJudge
from app.evaluation.schemas import EvalCase, EvalCaseResult, EvalReport
from app.workflows.service import SupportWorkflowService

ANSWER_SCORE_PASS_THRESHOLD = 0.7


class EvaluationRunner:
    def __init__(self, workflow: SupportWorkflowService, judge: AnswerJudge) -> None:
        self._workflow = workflow
        self._judge = judge

    async def run(self, session: AsyncSession, cases: list[EvalCase]) -> EvalReport:
        results = [await self._run_case(session, case) for case in cases]
        return self._aggregate(results)

    async def _run_case(self, session: AsyncSession, case: EvalCase) -> EvalCaseResult:
        state = await self._workflow.run(session, case.message)
        classification = state["classification"]
        response = state["response"]
        escalation = state["escalation"]

        category_correct = classification.category == case.expected_category
        escalation_correct = escalation == case.expected_escalation
        retrieval_hit = not case.expected_sources or any(
            source in response.sources for source in case.expected_sources
        )

        if case.expected_facts:
            verdict = await self._judge.judge(case.message, response.answer, case.expected_facts)
            answer_score, answer_reasoning = verdict.score, verdict.reasoning
        else:
            answer_score, answer_reasoning = 1.0, "no expected facts to grade"

        passed = (
            category_correct
            and retrieval_hit
            and escalation_correct
            and answer_score >= ANSWER_SCORE_PASS_THRESHOLD
        )

        return EvalCaseResult(
            case_id=case.id,
            category_correct=category_correct,
            retrieval_hit=retrieval_hit,
            escalation_correct=escalation_correct,
            answer_score=answer_score,
            answer_reasoning=answer_reasoning,
            passed=passed,
        )

    def _aggregate(self, results: list[EvalCaseResult]) -> EvalReport:
        n = len(results)
        return EvalReport(
            results=results,
            category_accuracy=sum(r.category_correct for r in results) / n,
            retrieval_hit_rate=sum(r.retrieval_hit for r in results) / n,
            escalation_accuracy=sum(r.escalation_correct for r in results) / n,
            mean_answer_score=sum(r.answer_score for r in results) / n,
            pass_rate=sum(r.passed for r in results) / n,
        )
