from typing import Any

from langgraph.graph import END, StateGraph

from chains.agent_nodes import (
    finalize_node,
    intent_parse_node,
    route_by_error_node,
    tool_execute_node,
    tool_select_node,
)
from chains.agent_state import AgentState
from services.agent_trace_service import agent_trace_service


def _after_select(state: AgentState) -> str:
    route = state.get("route", "continue")
    if route == "finalize":
        return "finalize"
    if route == "stop":
        return "finalize"
    return "execute"


def _after_route(state: AgentState) -> str:
    route = state.get("route", "continue")
    if route == "continue":
        return "select"
    return "finalize"


def create_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("intent_parse", intent_parse_node)
    graph.add_node("select", tool_select_node)
    graph.add_node("execute", tool_execute_node)
    graph.add_node("route_error", route_by_error_node)
    graph.add_node("finalize", finalize_node)

    graph.set_entry_point("intent_parse")
    graph.add_edge("intent_parse", "select")
    graph.add_conditional_edges("select", _after_select, {"execute": "execute", "finalize": "finalize"})
    graph.add_edge("execute", "route_error")
    graph.add_conditional_edges("route_error", _after_route, {"select": "select", "finalize": "finalize"})
    graph.add_edge("finalize", END)
    return graph.compile()


def run_react_agent(
    user_message: str,
    context: dict[str, Any] | None = None,
    tool_payloads: dict[str, dict[str, Any]] | None = None,
    max_loops: int = 6,
    pending_tools: list[str] | None = None,
    request_id: str | None = None,
    plan_id: str | None = None,
) -> dict[str, Any]:
    app = create_agent_graph()
    effective_request_id = request_id or ""
    effective_plan_id = plan_id or ""
    if effective_request_id:
        agent_trace_service.start_trace(
            effective_request_id,
            route="agent_graph",
            user_id=context.get("user_id") if isinstance(context, dict) else None,
            plan_id=effective_plan_id or None,
            metadata={"max_loops": max_loops},
        )
    init_state: AgentState = {
        "user_message": user_message,
        "context": context or {},
        "tool_payloads": tool_payloads or {},
        "request_id": effective_request_id,
        "plan_id": effective_plan_id,
        "pending_tools": pending_tools or [],
        "executed_tools": [],
        "steps": [],
        "retry_count": 0,
        "loop_count": 0,
        "max_loops": max_loops,
    }
    result = app.invoke(init_state)
    return {
        "message": "Agent 流程完成",
        "request_id": result.get("request_id", effective_request_id),
        "plan_id": result.get("plan_id", effective_plan_id),
        "final_answer": result.get("final_answer", ""),
        "steps": result.get("steps", []),
        "executed_tools": result.get("executed_tools", []),
        "route": result.get("route", "finalize"),
    }
