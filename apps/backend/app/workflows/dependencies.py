from functools import lru_cache

from app.agents.dependencies import get_classifier_agent, get_response_agent
from app.hallucination.dependencies import get_faithfulness_checker
from app.workflows.service import SupportWorkflowService


@lru_cache
def get_support_workflow_service() -> SupportWorkflowService:
    return SupportWorkflowService(
        classifier=get_classifier_agent(),
        responder=get_response_agent(),
        faithfulness_checker=get_faithfulness_checker(),
    )
