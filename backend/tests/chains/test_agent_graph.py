from chains.agent_graph import run_react_agent
from chains.agent_nodes import finalize_node
from services.agent_trace_service import agent_trace_service


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


def test_agent_graph_fills_partial_create_task_payload(monkeypatch):
    captured_payloads: list[dict] = []

    def fake_execute(tool_name: str, payload: dict):
        captured_payloads.append({"tool_name": tool_name, "payload": payload})
        return {"ok": True, "data": {"task_id": 88}}

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="幫我建立叫做 修登入 bug 的任務",
        context={"user_id": 1},
        tool_payloads={
            "create_task_for_user": {
                "data": {
                    "end_date": "2026-06-20T00:00:00",
                }
            }
        },
        pending_tools=["create_task_for_user"],
    )

    assert result["final_answer"] == "任務已完成，已依序執行工具流程。"
    assert captured_payloads[0]["payload"]["data"]["name"] == "修登入 bug"
    assert captured_payloads[0]["payload"]["data"]["end_date"] == "2026-06-20T00:00:00"
    assert captured_payloads[0]["payload"]["data"]["status"] == "pending"
    assert captured_payloads[0]["payload"]["data"]["priority"] == 2
    assert captured_payloads[0]["payload"]["data"]["task_remark"] == "幫我建立叫做 修登入 bug 的任務"


def test_agent_graph_sanitizes_nested_protected_fields(monkeypatch):
    captured_payloads: list[dict] = []

    def fake_execute(tool_name: str, payload: dict):
        captured_payloads.append({"tool_name": tool_name, "payload": payload})
        return {"ok": True, "data": {"task_id": 88}}

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="幫我建立任務",
        context={"user_id": 1},
        tool_payloads={
            "create_task_for_user": {
                "user_id": 999,
                "data": {
                    "name": "巢狀清理測試",
                    "end_date": "2026-06-20T00:00:00",
                    "nested": {"timeline_id": 77, "safe": "ok"},
                    "items": [{"task_id": 55, "name": "item"}],
                },
            }
        },
        pending_tools=["create_task_for_user"],
    )

    assert result["final_answer"] == "任務已完成，已依序執行工具流程。"
    payload = captured_payloads[0]["payload"]
    assert payload["user_id"] == 1
    assert "timeline_id" not in payload["data"]["nested"]
    assert payload["data"]["nested"]["safe"] == "ok"
    assert "task_id" not in payload["data"]["items"][0]


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


def test_agent_graph_create_task_missing_required_fields_routes_to_ask_user(monkeypatch):
    def fake_execute(tool_name: str, payload: dict):
        if tool_name == "create_task_for_user":
            assert payload["data"]["name"] == "整理面試題"
            assert "end_date" not in payload["data"]
            return {
                "ok": False,
                "error": {
                    "error_code": "VALIDATION_ERROR",
                    "message": "請提供標題和截止日期",
                    "retryable": False,
                    "hint": "請補齊欄位",
                },
            }
        return {"ok": True, "data": {}}

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="幫我建立叫做 整理面試題 的任務",
        context={"user_id": 1},
        tool_payloads={"create_task_for_user": {"data": {}}},
        pending_tools=["create_task_for_user"],
    )

    assert result["final_answer"] == "請補齊欄位"


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

    assert result["final_answer"] == "已建立專案「新專案」，並套用任務規劃，新增 2 個任務。"
    assert calls == [
        "create_timeline_for_user",
        "generate_timeline_tasks_with_ai",
        "batch_create_tasks_for_timeline",
    ]


def test_agent_graph_fills_missing_timeline_name_when_llm_payload_is_partial(monkeypatch):
    captured_payloads: list[dict] = []

    def fake_execute(tool_name: str, payload: dict):
        captured_payloads.append({"tool_name": tool_name, "payload": payload})
        if tool_name == "create_timeline_for_user":
            return {"ok": True, "data": {"timeline_id": 77}}
        return {"ok": True, "data": {}}

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="幫我建立叫做 Learnlink AI 協作 的專案",
        context={"user_id": 1},
        tool_payloads={
            "create_timeline_for_user": {
                "data": {
                    "remark": "由模型先草擬的說明",
                }
            }
        },
        pending_tools=["create_timeline_for_user"],
    )

    assert result["final_answer"] == "已建立專案「Learnlink AI 協作」。"
    assert captured_payloads[0]["tool_name"] == "create_timeline_for_user"
    assert captured_payloads[0]["payload"]["data"]["name"] == "Learnlink AI 協作"
    assert captured_payloads[0]["payload"]["data"]["remark"] == "由模型先草擬的說明"
    assert "start_date" not in captured_payloads[0]["payload"]["data"]
    assert "end_date" not in captured_payloads[0]["payload"]["data"]


def test_agent_graph_infers_project_name_from_learning_goal(monkeypatch):
    captured_payloads: list[dict] = []

    def fake_execute(tool_name: str, payload: dict):
        captured_payloads.append({"tool_name": tool_name, "payload": payload})
        return {"ok": True, "data": {"timeline_id": 77}}

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="幫我建立一個專案，主要為我學習langgraph的計畫",
        context={"user_id": 1},
        pending_tools=["create_timeline_for_user"],
    )

    assert result["final_answer"] == "已建立專案「LangGraph 學習計畫」。"
    assert captured_payloads[0]["payload"]["data"]["name"] == "LangGraph 學習計畫"


def test_agent_graph_passes_created_timeline_name_to_generation_step(monkeypatch):
    captured_payloads: list[dict] = []

    def fake_execute(tool_name: str, payload: dict):
        captured_payloads.append({"tool_name": tool_name, "payload": payload})
        if tool_name == "create_timeline_for_user":
            return {"ok": True, "data": {"timeline_id": 77}}
        if tool_name == "generate_timeline_tasks_with_ai":
            return {
                "ok": True,
                "data": {
                    "message": "ok",
                    "tasks": [],
                    "existingCount": 0,
                    "generatedCount": 0,
                },
            }
        return {"ok": True, "data": {}}

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="幫我建立一個專案，主要為我學習langgraph的計畫",
        context={"user_id": 1},
        pending_tools=["create_timeline_for_user", "generate_timeline_tasks_with_ai"],
    )

    assert result["final_answer"] == "已建立專案「LangGraph 學習計畫」。"
    assert captured_payloads[1]["tool_name"] == "generate_timeline_tasks_with_ai"
    assert captured_payloads[1]["payload"]["project_name"] == "LangGraph 學習計畫"


def test_agent_graph_summarizes_generated_task_suggestions(monkeypatch):
    def fake_execute(tool_name: str, _payload: dict):
        if tool_name == "create_timeline_for_user":
            return {"ok": True, "data": {"timeline_id": 77}}
        if tool_name == "generate_timeline_tasks_with_ai":
            return {
                "ok": True,
                "data": {
                    "message": "ok",
                    "tasks": [
                        {"name": "LangGraph 基礎概念", "isExisting": False},
                        {"name": "State 與 Node 練習", "isExisting": False},
                        {"name": "條件式路由實作", "isExisting": False},
                        {"name": "客服機器人專案", "isExisting": False},
                    ],
                    "existingCount": 0,
                    "generatedCount": 4,
                },
            }
        return {"ok": True, "data": {}}

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="幫我建立 LangGraph 學習專案，並先幫我規劃任務",
        context={"user_id": 1},
        pending_tools=["create_timeline_for_user", "generate_timeline_tasks_with_ai"],
    )

    assert result["final_answer"] == (
        "已建立專案「LangGraph 學習計畫」，AI 另外產生了 4 個任務建議，"
        "例如：LangGraph 基礎概念、State 與 Node 練習、條件式路由實作。"
    )


def test_agent_graph_fills_conflict_payload_from_update_payload(monkeypatch):
    captured_payloads: list[dict] = []

    def fake_execute(tool_name: str, payload: dict):
        captured_payloads.append({"tool_name": tool_name, "payload": payload})
        return {"ok": True, "data": {"ok": True}}

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="幫我看衝突",
        context={"user_id": 1, "timeline_id": 9},
        tool_payloads={
            "update_task_for_member": {
                "task_id": 11,
                "data": {
                    "name": "API 串接",
                    "start_date": "2026-06-18",
                    "end_date": "2026-06-20",
                    "priority": 3,
                },
            },
            "check_timeline_task_conflicts": {
                "payload": {
                    "include_ai_suggestion": False,
                }
            },
        },
        pending_tools=["check_timeline_task_conflicts"],
    )

    assert result["final_answer"] == "任務已完成，已依序執行工具流程。"
    assert captured_payloads[0]["payload"]["payload"] == {
        "task_id": 11,
        "name": "API 串接",
        "priority": 3,
        "start_date": "2026-06-18",
        "end_date": "2026-06-20",
        "include_ai_suggestion": False,
    }


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


def test_agent_graph_fills_update_payload_from_conflict_payload(monkeypatch):
    captured_payloads: list[dict] = []

    def fake_execute(tool_name: str, payload: dict):
        captured_payloads.append({"tool_name": tool_name, "payload": payload})
        return {"ok": True, "data": {"updated": True}}

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="更新任務排程",
        context={"user_id": 1, "task_id": 11},
        tool_payloads={
            "update_task_for_member": {
                "data": {
                    "priority": 1,
                }
            },
            "check_timeline_task_conflicts": {
                "payload": {
                    "name": "文件整理",
                    "start_date": "2026-06-10",
                    "end_date": "2026-06-12",
                }
            },
        },
        pending_tools=["update_task_for_member"],
    )

    assert result["final_answer"] == "任務已完成，已依序執行工具流程。"
    assert captured_payloads[0]["payload"]["task_id"] == 11
    assert captured_payloads[0]["payload"]["data"] == {
        "name": "文件整理",
        "priority": 1,
        "start_date": "2026-06-10",
        "end_date": "2026-06-12",
    }


def test_agent_graph_falls_back_to_generated_tasks_when_batch_payload_empty(monkeypatch):
    captured_payloads: list[dict] = []

    def fake_execute(tool_name: str, payload: dict):
        captured_payloads.append({"tool_name": tool_name, "payload": payload})
        if tool_name == "generate_timeline_tasks_with_ai":
            return {
                "ok": True,
                "data": {
                    "tasks": [
                        {"name": "Task A", "isExisting": False},
                        {"name": "Task B", "isExisting": False, "estimated_days": 5},
                    ]
                },
            }
        if tool_name == "batch_create_tasks_for_timeline":
            return {"ok": True, "data": {"result": {"created": 2}}}
        return {"ok": True, "data": {}}

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="建立任務",
        context={"user_id": 1, "timeline_id": 77},
        tool_payloads={
            "batch_create_tasks_for_timeline": {
                "tasks": [],
            }
        },
        pending_tools=["generate_timeline_tasks_with_ai", "batch_create_tasks_for_timeline"],
        max_loops=3,
    )

    assert result["final_answer"] == "已套用任務規劃，新增 2 個任務。"
    assert captured_payloads[1]["payload"]["tasks"] == [
        {"name": "Task A", "isExisting": False},
        {"name": "Task B", "isExisting": False, "estimated_days": 5},
    ]


def test_agent_graph_strips_generated_task_response_only_fields_for_batch_create(monkeypatch):
    captured_payloads: list[dict] = []

    def fake_execute(tool_name: str, payload: dict):
        captured_payloads.append({"tool_name": tool_name, "payload": payload})
        if tool_name == "generate_timeline_tasks_with_ai":
            return {
                "ok": True,
                "data": {
                    "tasks": [
                        {
                            "timeline_id": 39,
                            "completed": False,
                            "unknown": "drop me",
                            "isExisting": False,
                            "name": "Task A",
                            "priority": 2,
                            "status": "pending",
                            "estimated_days": 3,
                            "task_remark": "from AI",
                            "depends_on_task_refs": ["Task Before"],
                        },
                    ],
                },
            }
        if tool_name == "batch_create_tasks_for_timeline":
            return {"ok": True, "data": {"result": {"created": 1}}}
        return {"ok": True, "data": {}}

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="建立任務",
        context={"user_id": 1, "timeline_id": 39},
        tool_payloads={
            "batch_create_tasks_for_timeline": {
                "tasks": [],
            }
        },
        pending_tools=["generate_timeline_tasks_with_ai", "batch_create_tasks_for_timeline"],
        max_loops=3,
    )

    assert result["final_answer"] == "已套用任務規劃，新增 1 個任務。"
    assert captured_payloads[1]["payload"]["tasks"] == [
        {
            "isExisting": False,
            "name": "Task A",
            "priority": 2,
            "status": "pending",
            "estimated_days": 3,
            "task_remark": "from AI",
            "depends_on_task_refs": ["Task Before"],
        }
    ]


def test_agent_graph_preserves_malformed_conflict_payload_for_validation_error(monkeypatch):
    captured_payloads: list[dict] = []

    def fake_execute(tool_name: str, payload: dict):
        captured_payloads.append({"tool_name": tool_name, "payload": payload})
        return {
            "ok": False,
            "error": {
                "error_code": "VALIDATION_ERROR",
                "message": "請提供正確的 JSON 物件",
                "retryable": False,
                "hint": "請補齊欄位",
            },
        }

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="先檢查衝突",
        context={"user_id": 1, "timeline_id": 9},
        tool_payloads={
            "check_timeline_task_conflicts": {
                "payload": "bad-shape",
            }
        },
        pending_tools=["check_timeline_task_conflicts"],
    )

    assert captured_payloads[0]["payload"]["payload"] == "bad-shape"
    assert result["final_answer"] == "請補齊欄位"


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


def test_agent_graph_stops_retry_for_high_side_effect_tool(monkeypatch):
    calls: list[str] = []

    def fake_execute(tool_name: str, payload: dict):
        calls.append(tool_name)
        return {
            "ok": False,
            "error": {
                "error_code": "INTERNAL_ERROR",
                "message": "資料庫逾時",
                "retryable": True,
                "hint": "稍後再試",
            },
        }

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="幫我批次套用任務規劃",
        context={"user_id": 1, "timeline_id": 9},
        tool_payloads={"batch_create_tasks_for_timeline": {"tasks": []}},
        pending_tools=["batch_create_tasks_for_timeline"],
        max_loops=3,
    )

    assert calls == ["batch_create_tasks_for_timeline"]
    assert "可能已部分寫入" in result["final_answer"]


def test_agent_graph_retries_low_side_effect_tool(monkeypatch):
    calls: list[str] = []

    def fake_execute(tool_name: str, payload: dict):
        calls.append(tool_name)
        if len(calls) < 3:
            return {
                "ok": False,
                "error": {
                    "error_code": "INTERNAL_ERROR",
                    "message": "暫時失敗",
                    "retryable": True,
                    "hint": "稍後再試",
                },
            }
        return {"ok": True, "data": {"tasks": []}}

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="查詢任務",
        context={"user_id": 1},
        tool_payloads={"list_tasks_for_user": {"user_id": 1}},
        pending_tools=["list_tasks_for_user"],
        max_loops=5,
    )

    assert calls == ["list_tasks_for_user", "list_tasks_for_user", "list_tasks_for_user"]
    assert result["final_answer"] == "任務已完成，已依序執行工具流程。"


def test_agent_graph_records_trace_events_for_tool_execution(monkeypatch):
    agent_trace_service.clear()

    def fake_execute(tool_name: str, payload: dict):
        return {"ok": True, "data": {"tool_name": tool_name, "payload": payload}}

    monkeypatch.setattr("chains.agent_nodes.execute_registered_tool", fake_execute)

    result = run_react_agent(
        user_message="查詢任務",
        context={"user_id": 1},
        tool_payloads={"list_tasks_for_user": {"user_id": 1}},
        pending_tools=["list_tasks_for_user"],
        request_id="req_trace_test",
        plan_id="plan_trace_test",
    )

    trace = agent_trace_service.get_trace("req_trace_test")

    assert result["request_id"] == "req_trace_test"
    assert result["plan_id"] == "plan_trace_test"
    assert trace is not None
    tool_events = [event for event in trace["events"] if event["event_type"] == "tool_execution"]
    assert len(tool_events) == 1
    assert tool_events[0]["step_name"] == "list_tasks_for_user"
    assert tool_events[0]["status"] == "succeeded"
