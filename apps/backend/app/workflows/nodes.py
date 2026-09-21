from langgraph.runtime import Runtime

from app.agents.schemas import SupportResponse
from app.observability.tracing import get_tracer
from app.validation.rules import evaluate
from app.workflows.schemas import TicketState, WorkflowContext

CLARIFY_ANSWER = "Could you share a bit more detail about your issue so I can help?"


async def classify_node(state: TicketState, runtime: Runtime[WorkflowContext]) -> dict:
    with get_tracer().start_as_current_span("workflow.classify") as span:
        classification = await runtime.context.classifier.classify(state["message"])
        span.set_attribute("classification.category", classification.category)
        span.set_attribute("classification.priority", classification.priority)
        span.set_attribute("classification.sentiment", classification.sentiment)
    return {"classification": classification}


async def respond_node(state: TicketState, runtime: Runtime[WorkflowContext]) -> dict:
    with get_tracer().start_as_current_span("workflow.respond") as span:
        response = await runtime.context.responder.respond(runtime.context.session, state["message"])
        span.set_attribute("response.grounded", response.grounded)
        span.set_attribute("response.source_count", len(response.sources))
        if response.top_rerank_score is not None:
            span.set_attribute("response.top_rerank_score", response.top_rerank_score)
    return {"response": response}


async def clarify_node(state: TicketState) -> dict:
    with get_tracer().start_as_current_span("workflow.clarify"):
        pass
    return {"response": SupportResponse(answer=CLARIFY_ANSWER, sources=[], grounded=False)}


def route_after_classification(state: TicketState) -> str:
    return "clarify" if state["classification"].category == "other" else "respond"


async def check_faithfulness_node(state: TicketState, runtime: Runtime[WorkflowContext]) -> dict:
    response = state["response"]
    with get_tracer().start_as_current_span("workflow.check_faithfulness") as span:
        verdict = await runtime.context.faithfulness_checker.check(response.answer, response.context)
        span.set_attribute("faithfulness.is_faithful", verdict.is_faithful)
        span.set_attribute("faithfulness.unsupported_claim_count", len(verdict.unsupported_claims))
    return {"faithfulness": verdict}


async def validate_node(state: TicketState) -> dict:
    with get_tracer().start_as_current_span("workflow.validate") as span:
        result = evaluate(
            state["message"], state["classification"], state["response"], state["faithfulness"]
        )
        span.set_attribute("escalation.level", result.escalation.value)
        span.set_attribute("escalation.reason_count", len(result.reasons))
    return {"escalation": result.escalation, "escalation_reasons": result.reasons}
