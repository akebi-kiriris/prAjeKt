from chains.agent_graph import run_react_agent
from chains.agent_nodes import finalize_node


def test_agent_graph_runs_two_step_flow(monkeypatch):
    calls: list[str] = []

    def fake_execute(tool_name: str, payload: dict):
        calls.append(tool_name)
        return {"ok": True, "data": {"tool_name": tool_name, "payload": payload}}

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="幫我建立一個任務",
        context={"user_id": 1},
        tool_payloads={
            "create_task_for_user": {
                "user_id": 1,
                "data": {"name": "A", "end_date": "2026-06-01T00:00:00"},
            }
        },
    )

    assert result["message"] == "Agent 流程完成"
    assert len(result["steps"]) >= 2
    assert calls[:2] == ["list_tasks_for_user", "create_task_for_user"]


def test_agent_graph_routes_to_ask_user_on_validation_error(monkeypatch):
    calls: list[str] = []

    def fake_execute(tool_name: str, payload: dict):
        calls.append(tool_name)
        return {
            "ok": False,
            "error": {
                "error_code": "VALIDATION_ERROR",
                "message": "欄位錯誤",
                "retryable": False,
                "hint": "請補齊欄位",
            },
        }

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="幫我看衝突",
        context={"user_id": 1, "timeline_id": 9},
        tool_payloads={},
        max_loops=2,
    )

    assert "請補齊欄位" in result["final_answer"]
    assert len(calls) >= 1


def test_agent_graph_does_not_claim_done_for_write_intent_with_readonly_steps(monkeypatch):
    def fake_execute(_tool_name: str, _payload: dict):
        return {"ok": True, "data": {"tasks": []}}

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="幫我刪除雲端硬碟檔案",
        context={"user_id": 1},
        tool_payloads={},
    )

    assert "尚未支援此類需求" in result["final_answer"]


def test_agent_graph_rejects_unsupported_goal_without_false_success(monkeypatch):
    def fake_execute(_tool_name: str, _payload: dict):
        return {"ok": True, "data": {}}

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="請幫我寄 email 給老師",
        context={"user_id": 1},
        tool_payloads={},
    )

    assert "尚未支援此類需求" in result["final_answer"]
    assert result["executed_tools"] == []


def test_agent_graph_can_create_project_and_batch_create_dependency_tasks(monkeypatch):
    calls: list[str] = []

    def fake_execute(tool_name: str, _payload: dict):
        calls.append(tool_name)
        if tool_name == "create_timeline_for_user":
            return {"ok": True, "data": {"timeline_id": 77}}
        if tool_name == "generate_timeline_tasks_with_ai":
            return {
                "ok": True,
                "data": {
                    "message": "ok",
                    "tasks": [
                        {"name": "Task A", "isExisting": False},
                        {"name": "Task B", "isExisting": False, "depends_on_task_refs": ["Task A"]},
                    ],
                    "existingCount": 0,
                    "generatedCount": 2,
                },
            }
        if tool_name == "batch_create_tasks_for_timeline":
            return {"ok": True, "data": {"result": {"created": 2}}}
        return {"ok": True, "data": {}}

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="幫我創建專案並建立有依賴鍊的任務",
        context={"user_id": 1},
        tool_payloads={},
    )

    assert result["final_answer"] == "任務已完成，已依序執行工具流程。"
    assert calls == [
        "create_timeline_for_user",
        "generate_timeline_tasks_with_ai",
        "batch_create_tasks_for_timeline",
    ]


def test_agent_graph_can_check_conflict_before_update_task(monkeypatch):
    calls: list[str] = []

    def fake_execute(tool_name: str, payload: dict):
        calls.append(tool_name)
        if tool_name == "list_tasks_for_user":
            return {"ok": True, "data": {"tasks": [{"task_id": 11, "name": "A"}]}}
        if tool_name == "check_timeline_task_conflicts":
            return {"ok": True, "data": {"result": {"has_conflict": False}}}
        if tool_name == "update_task_for_member":
            return {"ok": True, "data": {"updated": True, "task_id": 11}}
        return {"ok": True, "data": {}}

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="先幫我檢查衝突再更新任務截止日",
        context={"user_id": 1, "timeline_id": 9},
        tool_payloads={
            "update_task_for_member": {
                "task_id": 11,
                "data": {"end_date": "2026-06-20"},
            },
            "check_timeline_task_conflicts": {
                "payload": {
                    "task_id": 11,
                    "name": "A",
                    "start_date": "2026-06-18",
                    "end_date": "2026-06-20",
                    "include_ai_suggestion": False,
                }
            },
        },
    )

    assert result["final_answer"] == "任務已完成，已依序執行工具流程。"
    assert calls == [
        "list_tasks_for_user",
        "check_timeline_task_conflicts",
        "update_task_for_member",
    ]


def test_finalize_node_handles_malformed_steps_without_crashing():
    result = finalize_node(
        {
            "steps": ["broken-step"],
            "route": "finalize",
            "requires_write": True,
            "unsupported_goal": False,
        }
    )

    assert result["final_answer"] == "目前只完成查詢工具，尚未執行任何寫入操作；請補充可建立/更新所需資訊。"
