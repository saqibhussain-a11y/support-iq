from functools import lru_cache

from app.hallucination.checker import FaithfulnessChecker
from app.llm.dependencies import get_llm_service


@lru_cache
def get_faithfulness_checker() -> FaithfulnessChecker:
    return FaithfulnessChecker(llm_service=get_llm_service())
