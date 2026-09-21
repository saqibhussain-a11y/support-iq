import pytest

from app.agents.schemas import SupportResponse, TicketClassification
from app.evaluation.runner import EvaluationRunner
from app.evaluation.schemas import EvalCase, JudgeVerdict
from app.validation.schemas import EscalationLevel


class FakeWorkflowService:
    def __init__(self, state: dict) -> None:
        self.state = state
        self.received_messages: list[str] = []

    async def run(self, session, message: str) -> dict:
        self.received_messages.append(message)
        return self.state


class FakeJudge:
    def __init__(self, verdict: JudgeVerdict) -> None:
        self.verdict = verdict
        self.called = False

    async def judge(self, question, answer, expected_facts):
        self.called = True
        return self.verdict


def make_state(category="billing", escalation=EscalationLevel.NONE, sources=("refund_policy.md",)) -> dict:
    return {
        "message": "irrelevant",
        "classification": TicketClassification(category=category, priority="high", sentiment="neutral"),
        "response": SupportResponse(answer="the answer", sources=list(sources), grounded=True),
        "escalation": escalation,
        "escalation_reasons": [],
    }


def make_case(**overrides) -> EvalCase:
    defaults = dict(
        id="case-1",
        message="some question",
        expected_category="billing",
        expected_escalation=EscalationLevel.NONE,
        expected_sources=["refund_policy.md"],
        expected_facts=["some fact"],
    )
    defaults.update(overrides)
    return EvalCase(**defaults)


@pytest.mark.asyncio
async def test_case_passes_when_everything_matches():
    workflow = FakeWorkflowService(make_state())
    judge = FakeJudge(JudgeVerdict(score=0.9, reasoning="good"))
    runner = EvaluationRunner(workflow=workflow, judge=judge)

    report = await runner.run(session=object(), cases=[make_case()])

    result = report.results[0]
    assert result.category_correct is True
    assert result.retrieval_hit is True
    assert result.escalation_correct is True
    assert result.answer_score == 0.9
    assert result.passed is True
    assert judge.called is True


@pytest.mark.asyncio
async def test_case_fails_on_category_mismatch():
    workflow = FakeWorkflowService(make_state(category="account"))
    judge = FakeJudge(JudgeVerdict(score=1.0, reasoning="good"))
    runner = EvaluationRunner(workflow=workflow, judge=judge)

    report = await runner.run(session=object(), cases=[make_case()])

    assert report.results[0].category_correct is False
    assert report.results[0].passed is False


@pytest.mark.asyncio
async def test_case_fails_on_retrieval_miss():
    workflow = FakeWorkflowService(make_state(sources=("unrelated.md",)))
    judge = FakeJudge(JudgeVerdict(score=1.0, reasoning="good"))
    runner = EvaluationRunner(workflow=workflow, judge=judge)

    report = await runner.run(session=object(), cases=[make_case()])

    assert report.results[0].retrieval_hit is False
    assert report.results[0].passed is False


@pytest.mark.asyncio
async def test_case_fails_on_escalation_mismatch():
    workflow = FakeWorkflowService(make_state(escalation=EscalationLevel.REVIEW))
    judge = FakeJudge(JudgeVerdict(score=1.0, reasoning="good"))
    runner = EvaluationRunner(workflow=workflow, judge=judge)

    report = await runner.run(session=object(), cases=[make_case()])

    assert report.results[0].escalation_correct is False
    assert report.results[0].passed is False


@pytest.mark.asyncio
async def test_case_fails_when_answer_score_below_threshold():
    workflow = FakeWorkflowService(make_state())
    judge = FakeJudge(JudgeVerdict(score=0.4, reasoning="missing key facts"))
    runner = EvaluationRunner(workflow=workflow, judge=judge)

    report = await runner.run(session=object(), cases=[make_case()])

    assert report.results[0].passed is False


@pytest.mark.asyncio
async def test_empty_expected_sources_skips_retrieval_check():
    workflow = FakeWorkflowService(make_state(sources=()))
    judge = FakeJudge(JudgeVerdict(score=1.0, reasoning="good"))
    runner = EvaluationRunner(workflow=workflow, judge=judge)

    report = await runner.run(session=object(), cases=[make_case(expected_sources=[])])

    assert report.results[0].retrieval_hit is True


@pytest.mark.asyncio
async def test_empty_expected_facts_skips_judge_call():
    workflow = FakeWorkflowService(make_state())
    judge = FakeJudge(JudgeVerdict(score=0.0, reasoning="should not be used"))
    runner = EvaluationRunner(workflow=workflow, judge=judge)

    report = await runner.run(session=object(), cases=[make_case(expected_facts=[])])

    assert judge.called is False
    assert report.results[0].answer_score == 1.0


@pytest.mark.asyncio
async def test_report_aggregates_metrics_across_cases():
    workflow = FakeWorkflowService(make_state())
    judge = FakeJudge(JudgeVerdict(score=1.0, reasoning="good"))
    runner = EvaluationRunner(workflow=workflow, judge=judge)

    passing_case = make_case(id="pass")
    failing_case = make_case(id="fail", expected_category="account")

    report = await runner.run(session=object(), cases=[passing_case, failing_case])

    assert report.category_accuracy == 0.5
    assert report.pass_rate == 0.5
    assert report.mean_answer_score == 1.0
