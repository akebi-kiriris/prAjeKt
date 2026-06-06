from services.tool_plan_service import propose_plan_with_llm


def test_propose_plan_prompt_includes_intent_boundaries(monkeypatch):
    captured: dict[str, str] = {}

    class _FakeLlm:
        def invoke(self, prompt: str):
            captured["prompt"] = prompt
            return type(
                "FakeResponse",
                (),
                {
                    "content": '{"supported": true, "planning_mode": "create_project_only", "steps": ["create_timeline_for_user"], "payload_draft": {}, "reason": "只建立專案"}'
                },
            )()

    monkeypatch.setattr("chains.get_default_llm", lambda provider: _FakeLlm())

    propose_plan_with_llm(
        user_message="幫我建立一個 LangGraph 學習專案",
        context={"user_id": 1},
        tools=[
            {
                "name": "create_timeline_for_user",
                "description": "建立專案",
                "side_effect_level": "high",
                "permission_note": "需登入使用者身份。",
                "planner_role": "direct_write",
                "workflow_group": "timeline_task_planning",
                "completes_after": "",
                "input_schema": {"type": "object"},
            },
            {
                "name": "generate_timeline_tasks_with_ai",
                "description": "AI 生成任務草案",
                "side_effect_level": "medium",
                "permission_note": "需可讀取該專案脈絡。",
                "planner_role": "suggestion",
                "workflow_group": "timeline_task_planning",
                "completes_after": "",
                "input_schema": {"type": "object"},
            },
            {
                "name": "batch_create_tasks_for_timeline",
                "description": "批次建立任務",
                "side_effect_level": "high",
                "permission_note": "需專案成員權限。",
                "planner_role": "apply_suggestion",
                "workflow_group": "timeline_task_planning",
                "completes_after": "generate_timeline_tasks_with_ai",
                "input_schema": {"type": "object"},
            },
        ],
    )

    prompt = captured["prompt"]
    assert "planner_role=suggestion" in prompt
    assert "planner_role=apply_suggestion" in prompt
    assert "workflow_group=timeline_task_planning" in prompt
    assert "completes_after=generate_timeline_tasks_with_ai" in prompt
    assert "如果只是要建立專案：planning_mode=create_project_only" in prompt
    assert "如果是建立專案後先產生任務建議" in prompt
    assert "你還必須輸出 planning_mode" in prompt
    assert "如果使用者要你把規劃結果直接建立成任務" in prompt
    assert "如果使用者要求的是『實際把結果建立/更新到系統內』" in prompt
    assert "不要使用『新專案』這種空泛名稱" in prompt
