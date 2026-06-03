from services import copilot_service
from services.tool_plan_service import ToolPlanError


def test_create_copilot_agent_plan_returns_preview():
    payload = copilot_service.create_copilot_agent_plan(
        "幫我建立專案並產生任務",
        user_id=1,
        context={"user_id": 1},
    )

    assert payload["ok"] is True
    assert payload["status"] == "planned"
    assert payload["plan_id"].startswith("plan_")
    assert len(payload["steps_preview"]) >= 1
    assert payload["proposal_source"] in {"llm_proposal", "rule_fallback"}


def test_create_plan_uses_llm_proposal_when_available(monkeypatch):
    def fake_propose(*, user_message: str, context: dict, tools: list[dict]):
        return {
            "steps": ["list_tasks_for_user", "create_task_for_user"],
            "payload_draft": {"create_task_for_user": {"title": "A"}},
            "reason": "依需求先查詢後建立",
        }

    monkeypatch.setattr(copilot_service, "propose_plan_with_llm", fake_propose)
    payload = copilot_service.create_copilot_agent_plan(
        "先看任務再建立",
        user_id=7,
        context={"user_id": 7},
    )

    assert payload["proposal_source"] == "llm_proposal"
    assert payload["proposal_reason"] == "依需求先查詢後建立"


def test_create_plan_fallbacks_to_rule_when_llm_plan_failed(monkeypatch):
    def fake_propose(*, user_message: str, context: dict, tools: list[dict]):
        raise ToolPlanError("mock llm failed")

    monkeypatch.setattr(copilot_service, "propose_plan_with_llm", fake_propose)
    payload = copilot_service.create_copilot_agent_plan(
        "幫我建立專案並產生任務",
        user_id=8,
        context={"user_id": 8},
    )

    assert payload["proposal_source"] == "rule_fallback"
    assert "模型提案失敗" in (payload.get("proposal_reason") or "")
    assert len(payload["steps_preview"]) >= 1


def test_create_plan_force_model_proposal_raises_when_llm_failed(monkeypatch):
    def fake_propose(*, user_message: str, context: dict, tools: list[dict]):
        raise ToolPlanError("mock llm failed")

    monkeypatch.setattr(copilot_service, "propose_plan_with_llm", fake_propose)
    try:
        copilot_service.create_copilot_agent_plan(
            "重規劃需求",
            user_id=9,
            context={"user_id": 9},
            force_model_proposal=True,
        )
        assert False, "should raise"
    except copilot_service.CopilotOperationError as err:
        assert err.status_code == 409
        assert "模型重規劃失敗" in err.message


def test_execute_copilot_agent_plan_uses_approved_tools(monkeypatch):
    created = copilot_service.create_copilot_agent_plan(
        "幫我建立專案並產生任務",
        user_id=2,
        context={"user_id": 2},
    )
    captured: dict[str, object] = {}

    def fake_execute(
        user_message: str,
        context: dict | None = None,
        tool_payloads: dict | None = None,
        max_loops: int = 6,
        approved_pending_tools: list[str] | None = None,
    ):
        captured["approved_pending_tools"] = approved_pending_tools
        return {
            "message": "Agent 流程完成",
            "final_answer": "任務已完成",
            "steps": [{"tool_name": "create_timeline_for_user", "input": {}, "output": {"ok": True}}],
            "executed_tools": ["create_timeline_for_user"],
            "route": "finalize",
        }

    monkeypatch.setattr(copilot_service, "execute_copilot_agent_request", fake_execute)
    result = copilot_service.execute_copilot_agent_plan(
        plan_id=created["plan_id"],
        user_id=2,
        confirm=True,
    )

    assert result["ok"] is True
    assert result["status"] == "succeeded"
    assert isinstance(captured["approved_pending_tools"], list)


def test_reject_plan_blocks_execution(monkeypatch):
    created = copilot_service.create_copilot_agent_plan(
        "幫我建立任務",
        user_id=3,
        context={"user_id": 3},
    )
    copilot_service.reject_copilot_agent_plan(created["plan_id"], user_id=3)

    try:
        copilot_service.execute_copilot_agent_plan(
            plan_id=created["plan_id"],
            user_id=3,
            confirm=True,
        )
        assert False, "should raise"
    except copilot_service.CopilotOperationError as err:
        assert err.status_code == 409


def test_execute_plan_rejects_runtime_tool_payload_override(monkeypatch):
    created = copilot_service.create_copilot_agent_plan(
        "幫我建立專案",
        user_id=4,
        context={"user_id": 4},
    )
    try:
        copilot_service.execute_copilot_agent_plan(
            plan_id=created["plan_id"],
            user_id=4,
            confirm=True,
            tool_payloads={"create_timeline_for_user": {"user_id": 999}},
        )
        assert False, "should raise"
    except copilot_service.CopilotOperationError as err:
        assert err.status_code == 409


def test_execute_plan_cannot_run_twice(monkeypatch):
    created = copilot_service.create_copilot_agent_plan(
        "幫我建立專案",
        user_id=5,
        context={"user_id": 5},
    )

    def fake_execute(
        user_message: str,
        context: dict | None = None,
        tool_payloads: dict | None = None,
        max_loops: int = 6,
        approved_pending_tools: list[str] | None = None,
    ):
        return {
            "message": "Agent 流程完成",
            "final_answer": "任務已完成",
            "steps": [{"tool_name": "create_timeline_for_user", "input": {}, "output": {"ok": True}}],
            "executed_tools": ["create_timeline_for_user"],
            "route": "finalize",
        }

    monkeypatch.setattr(copilot_service, "execute_copilot_agent_request", fake_execute)
    first = copilot_service.execute_copilot_agent_plan(
        plan_id=created["plan_id"],
        user_id=5,
        confirm=True,
    )
    assert first["status"] == "succeeded"

    try:
        copilot_service.execute_copilot_agent_plan(
            plan_id=created["plan_id"],
            user_id=5,
            confirm=True,
        )
        assert False, "should raise"
    except copilot_service.CopilotOperationError as err:
        assert err.status_code == 409


def test_plan_confirm_flow_keeps_update_conflict_tool_order(monkeypatch):
    created = copilot_service.create_copilot_agent_plan(
        "先檢查衝突再更新任務",
        user_id=6,
        context={"user_id": 6, "timeline_id": 9},
        tool_payloads={
            "update_task_for_member": {"task_id": 99, "data": {"status": "in_progress"}},
            "check_timeline_task_conflicts": {"payload": {"task_id": 99, "name": "T"}},
        },
    )
    captured: dict[str, object] = {}

    def fake_execute(
        user_message: str,
        context: dict | None = None,
        tool_payloads: dict | None = None,
        max_loops: int = 6,
        approved_pending_tools: list[str] | None = None,
    ):
        captured["approved_pending_tools"] = approved_pending_tools
        return {
            "message": "Agent 流程完成",
            "final_answer": "任務已完成",
            "steps": [{"tool_name": "update_task_for_member", "input": {}, "output": {"ok": True}}],
            "executed_tools": approved_pending_tools or [],
            "route": "finalize",
        }

    monkeypatch.setattr(copilot_service, "execute_copilot_agent_request", fake_execute)
    result = copilot_service.execute_copilot_agent_plan(
        plan_id=created["plan_id"],
        user_id=6,
        confirm=True,
    )

    assert result["ok"] is True
    assert captured["approved_pending_tools"] == [
        "list_tasks_for_user",
        "check_timeline_task_conflicts",
        "update_task_for_member",
    ]
