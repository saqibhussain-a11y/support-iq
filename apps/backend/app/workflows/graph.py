from functools import lru_cache

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.observability.tracing import configure_langsmith
from app.workflows.nodes import (
    check_faithfulness_node,
    classify_node,
    clarify_node,
    respond_node,
    route_after_classification,
    validate_node,
)
from app.workflows.schemas import TicketState, WorkflowContext


@lru_cache
def build_support_workflow() -> CompiledStateGraph:
    configure_langsmith()
    graph = StateGraph(TicketState, context_schema=WorkflowContext)
    graph.add_node("classify", classify_node)
    graph.add_node("respond", respond_node)
    graph.add_node("clarify", clarify_node)
    graph.add_node("check_faithfulness", check_faithfulness_node)
    graph.add_node("validate", validate_node)
    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify", route_after_classification, {"respond": "respond", "clarify": "clarify"}
    )
    graph.add_edge("respond", "check_faithfulness")
    graph.add_edge("check_faithfulness", "validate")
    graph.add_edge("clarify", "validate")
    graph.add_edge("validate", END)
    return graph.compile()
