from functools import lru_cache

from app.agents.dependencies import get_classifier_agent, get_response_agent
from app.workflows.service import SupportWorkflowService


@lru_cache
def get_support_workflow_service() -> SupportWorkflowService:
    return SupportWorkflowService(
        classifier=get_classifier_agent(),
        responder=get_response_agent(),
    )
