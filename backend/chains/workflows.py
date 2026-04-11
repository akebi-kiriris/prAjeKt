"""LangGraph workflows for PrAjeKt AI flows.

此模組提供 Phase 6.6 起始的 LangGraph 節點編排最小範本。
目前（Phase 6.6）未被使用，等待 Phase 7 需要複雜多步工作流時再啟動。

何時應激活此模組：
1. 需要條件分支路由（例如根據用戶輸入走不同工具）
2. 需要多步工作流（例如規劃 → 執行 → 驗證 → 修正）
3. 需要循環或自動重試邏輯
4. 需要人類介入節點（審核 AI 決策）

目前簡單的 chain 架構足以應對單步驟 LLM 調用。
"""

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from chains.tool_selection_chain import select_tools


class ToolRoutingState(TypedDict, total=False):
    user_input: str
    available_tools: list[dict[str, str]]
    context: dict[str, Any]
    selection: dict[str, Any]


def _select_tool_node(state: ToolRoutingState, llm: Any) -> ToolRoutingState:
    selection = select_tools(
        llm=llm,
        user_input=state.get("user_input", ""),
        available_tools=state.get("available_tools", []),
        context=state.get("context", {}),
    )
    return {"selection": selection}


def create_tool_routing_workflow(llm: Any):
    """建立工具路由 LangGraph 工作流（單節點最小可用版）。
    
    目前實況：僅為範本，未被服務層使用。
    Phase 7 若需多步工作流時應改為呼叫此方法。
    """
    graph = StateGraph(ToolRoutingState)
    graph.add_node("select_tool", lambda state: _select_tool_node(state, llm))
    graph.set_entry_point("select_tool")
    graph.add_edge("select_tool", END)
    return graph.compile()
