from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.supervisor import supervisor_node
from app.agents.validator import validate_response
from app.agents.workers import (
    query_agent_node,
    report_agent_node,
    compliance_agent_node,
    forecast_agent_node,
    rag_agent_node,
)
import structlog

logger = structlog.get_logger()

MAX_ITERATIONS = 5


def route_to_agent(state: AgentState) -> str:
    if state.get("iteration_count", 0) >= MAX_ITERATIONS:
        logger.warning("Max iterations reached, forcing END")
        return END

    target = state.get("target_agent", "query_agent")
    valid = ["query_agent", "report_agent", "compliance_agent", "forecast_agent", "rag_agent"]

    if target not in valid:
        logger.warning("Unknown target agent, defaulting", target=target)
        return "query_agent"

    return target


def build_sis_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("query_agent", query_agent_node)
    graph.add_node("report_agent", report_agent_node)
    graph.add_node("compliance_agent", compliance_agent_node)
    graph.add_node("forecast_agent", forecast_agent_node)
    graph.add_node("rag_agent", rag_agent_node)
    graph.add_node("validator", validate_response)

    # Entry point
    graph.set_entry_point("supervisor")

    # Supervisor routes to worker
    graph.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "query_agent": "query_agent",
            "report_agent": "report_agent",
            "compliance_agent": "compliance_agent",
            "forecast_agent": "forecast_agent",
            "rag_agent": "rag_agent",
            END: END,
        }
    )

    # All workers go to validator
    for agent in ["query_agent", "report_agent", "compliance_agent", "forecast_agent", "rag_agent"]:
        graph.add_edge(agent, "validator")

    # Validator goes to END
    graph.add_edge("validator", END)

    return graph.compile()


# Singleton graph instance
sis_graph = build_sis_graph()
