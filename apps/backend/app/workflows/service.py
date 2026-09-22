from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.classifier import ClassifierAgent
from app.agents.response import ResponseAgent
from app.hallucination.checker import FaithfulnessChecker
from app.workflows.graph import build_support_workflow
from app.workflows.schemas import TicketState, WorkflowContext


class SupportWorkflowService:
    def __init__(
        self,
        classifier: ClassifierAgent,
        responder: ResponseAgent,
        faithfulness_checker: FaithfulnessChecker,
    ) -> None:
        self._classifier = classifier
        self._responder = responder
        self._faithfulness_checker = faithfulness_checker
        self._graph = build_support_workflow()

    def _new_run(self, session: AsyncSession, message: str) -> tuple[WorkflowContext, TicketState]:
        context = WorkflowContext(
            classifier=self._classifier,
            responder=self._responder,
            faithfulness_checker=self._faithfulness_checker,
            session=session,
        )
        initial_state: TicketState = {
            "message": message,
            "classification": None,
            "response": None,
            "faithfulness": None,
            "escalation": None,
            "escalation_reasons": [],
        }
        return context, initial_state

    async def run(self, session: AsyncSession, message: str) -> TicketState:
        context, initial_state = self._new_run(session, message)
        return await self._graph.ainvoke(initial_state, context=context)

    async def run_stream(self, session: AsyncSession, message: str) -> AsyncIterator[dict]:
        context, initial_state = self._new_run(session, message)
        async for mode, chunk in self._graph.astream(
            initial_state, context=context, stream_mode=["updates", "custom"]
        ):
            if mode == "updates":
                for node_name, update in chunk.items():
                    yield {"kind": "stage", "stage": node_name, "update": update}
            else:
                yield chunk
