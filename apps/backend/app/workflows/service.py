from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.classifier import ClassifierAgent
from app.agents.response import ResponseAgent
from app.workflows.graph import build_support_workflow
from app.workflows.schemas import TicketState, WorkflowContext


class SupportWorkflowService:
    def __init__(self, classifier: ClassifierAgent, responder: ResponseAgent) -> None:
        self._classifier = classifier
        self._responder = responder
        self._graph = build_support_workflow()

    async def run(self, session: AsyncSession, message: str) -> TicketState:
        context = WorkflowContext(classifier=self._classifier, responder=self._responder, session=session)
        initial_state: TicketState = {
            "message": message,
            "classification": None,
            "response": None,
            "escalation": None,
            "escalation_reasons": [],
        }
        return await self._graph.ainvoke(initial_state, context=context)
