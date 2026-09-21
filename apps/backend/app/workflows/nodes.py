from langgraph.runtime import Runtime

from app.agents.schemas import SupportResponse
from app.validation.rules import evaluate
from app.workflows.schemas import TicketState, WorkflowContext

CLARIFY_ANSWER = "Could you share a bit more detail about your issue so I can help?"


async def classify_node(state: TicketState, runtime: Runtime[WorkflowContext]) -> dict:
    classification = await runtime.context.classifier.classify(state["message"])
    return {"classification": classification}


async def respond_node(state: TicketState, runtime: Runtime[WorkflowContext]) -> dict:
    response = await runtime.context.responder.respond(runtime.context.session, state["message"])
    return {"response": response}


async def clarify_node(state: TicketState) -> dict:
    return {"response": SupportResponse(answer=CLARIFY_ANSWER, sources=[], grounded=False)}


def route_after_classification(state: TicketState) -> str:
    return "clarify" if state["classification"].category == "other" else "respond"


async def validate_node(state: TicketState) -> dict:
    result = evaluate(state["message"], state["classification"], state["response"])
    return {"escalation": result.escalation, "escalation_reasons": result.reasons}
