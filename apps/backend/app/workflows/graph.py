from functools import lru_cache

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.workflows.nodes import classify_node, clarify_node, respond_node, route_after_classification
from app.workflows.schemas import TicketState, WorkflowContext


@lru_cache
def build_support_workflow() -> CompiledStateGraph:
    graph = StateGraph(TicketState, context_schema=WorkflowContext)
    graph.add_node("classify", classify_node)
    graph.add_node("respond", respond_node)
    graph.add_node("clarify", clarify_node)
    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify", route_after_classification, {"respond": "respond", "clarify": "clarify"}
    )
    graph.add_edge("respond", END)
    graph.add_edge("clarify", END)
    return graph.compile()
