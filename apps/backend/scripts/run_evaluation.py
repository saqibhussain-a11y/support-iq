import asyncio

from app.db.session import session_scope
from app.evaluation.dataset import EVAL_CASES
from app.evaluation.dependencies import get_evaluation_runner


async def main() -> None:
    runner = get_evaluation_runner()

    async with session_scope() as session:
        report = await runner.run(session, EVAL_CASES)

    for result in report.results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.case_id}")
        print(f"  category_correct={result.category_correct}  retrieval_hit={result.retrieval_hit}  "
              f"escalation_correct={result.escalation_correct}  answer_score={result.answer_score:.2f}")
        print(f"  judge: {result.answer_reasoning}")
        print()

    print("Summary:")
    print(f"  category_accuracy:  {report.category_accuracy:.0%}")
    print(f"  retrieval_hit_rate: {report.retrieval_hit_rate:.0%}")
    print(f"  escalation_accuracy: {report.escalation_accuracy:.0%}")
    print(f"  mean_answer_score:  {report.mean_answer_score:.2f}")
    print(f"  pass_rate:          {report.pass_rate:.0%}")


if __name__ == "__main__":
    asyncio.run(main())
