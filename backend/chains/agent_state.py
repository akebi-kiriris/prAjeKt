from typing import Any, Literal, TypedDict


RouteType = Literal["continue", "retry", "ask_user", "stop", "finalize"]


class AgentStep(TypedDict):
    tool_name: str
    input: dict[str, Any]
    output: dict[str, Any]


class AgentState(TypedDict, total=False):
    user_message: str
    context: dict[str, Any]
    tool_payloads: dict[str, dict[str, Any]]
    pending_tools: list[str]
    executed_tools: list[str]
    steps: list[AgentStep]
    last_result: dict[str, Any]
    last_error: dict[str, Any]
    last_tool_name: str
    route: RouteType
    ask_user_message: str
    final_answer: str
    retry_count: int
    loop_count: int
    max_loops: int
    requires_write: bool
    unsupported_goal: bool
    created_timeline_id: int
