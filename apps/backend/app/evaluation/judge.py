from app.evaluation.schemas import JudgeVerdict
from app.llm.schemas import ChatMessage
from app.llm.service import LLMService

JUDGE_SYSTEM_PROMPT = (
    "You are grading a customer support response for factual correctness. You will be given the "
    "customer's question, the assistant's answer, and a list of facts the answer is expected to "
    "convey. Score how well the answer conveys those facts, from 0.0 (missing or contradicts them) "
    "to 1.0 (conveys all of them accurately). Do not penalize extra helpful detail, wording "
    "differences, or a different tone. Respond with strict JSON only: "
    '{"score": <float 0.0-1.0>, "reasoning": "<one sentence>"}'
)


class AnswerJudge:
    def __init__(self, llm_service: LLMService) -> None:
        self._llm_service = llm_service

    async def judge(self, question: str, answer: str, expected_facts: list[str]) -> JudgeVerdict:
        facts_block = "\n".join(f"- {fact}" for fact in expected_facts)
        messages = [
            ChatMessage(role="system", content=JUDGE_SYSTEM_PROMPT),
            ChatMessage(
                role="user",
                content=(
                    f"Question: {question}\n\nAnswer: {answer}\n\nExpected facts:\n{facts_block}"
                ),
            ),
        ]
        return await self._llm_service.complete_structured(messages, JudgeVerdict, temperature=0.0)
