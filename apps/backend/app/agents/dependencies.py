from functools import lru_cache

from app.agents.classifier import ClassifierAgent
from app.agents.response import ResponseAgent
from app.llm.dependencies import get_llm_service
from app.retrieval.dependencies import get_retrieval_service


@lru_cache
def get_classifier_agent() -> ClassifierAgent:
    return ClassifierAgent(llm_service=get_llm_service())


@lru_cache
def get_response_agent() -> ResponseAgent:
    return ResponseAgent(
        llm_service=get_llm_service(),
        retrieval_service=get_retrieval_service(),
    )
