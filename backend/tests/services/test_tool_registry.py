from services.tools import registry


def test_list_registered_tools_contains_phase9_3_whitelist():
    tools = registry.list_registered_tools()
    tool_names = {item["name"] for item in tools}
    assert "create_task_for_user" in tool_names
    assert "list_tasks_for_user" in tool_names
    assert "upload_and_index_knowledge_document" in tool_names


def test_execute_registered_tool_returns_not_found_for_unknown_tool():
    result = registry.execute_registered_tool("unknown_tool", {})
    assert result["ok"] is False
    assert result["error"]["error_code"] == "NOT_FOUND"


def test_execute_registered_tool_delegates_handler(monkeypatch):
    def fake_handler(payload):
        return {"ok": True, "data": {"echo": payload}}

    fake_tool = registry.ToolDefinition(
        name="fake_tool",
        description="fake",
        input_model=object,
        handler=fake_handler,
        side_effects="none",
        side_effect_level="low",
        user_visible_label="假工具",
        requires_confirmation=False,
        permission_note="none",
    )
    monkeypatch.setitem(registry.TOOL_REGISTRY, "fake_tool", fake_tool)

    result = registry.execute_registered_tool("fake_tool", {"x": 1})
    assert result["ok"] is True
    assert result["data"]["echo"] == {"x": 1}


def test_list_registered_tools_raises_in_strict_mode_when_docstring_missing(monkeypatch):
    def handler_without_docstring(payload):
        return {"ok": True, "data": payload}

    fake_tool = registry.ToolDefinition(
        name="strict_tool",
        description=None,
        input_model=object,
        handler=handler_without_docstring,
        side_effects="none",
        side_effect_level="low",
        user_visible_label="嚴格測試工具",
        requires_confirmation=False,
        permission_note="none",
    )
    monkeypatch.setitem(registry.TOOL_REGISTRY, "strict_tool", fake_tool)
    monkeypatch.setenv("PRAJEKT_TOOL_DOCSTRING_STRICT", "true")

    try:
        registry.list_registered_tools()
        assert False, "strict mode 應該在缺 docstring 時拋錯"
    except ValueError as exc:
        assert "strict_tool" in str(exc)


def test_execute_registered_tool_maps_handler_exception(monkeypatch):
    def broken_handler(_payload):
        raise RuntimeError("boom")

    fake_tool = registry.ToolDefinition(
        name="broken_tool",
        description="broken",
        input_model=object,
        handler=broken_handler,
        side_effects="none",
        side_effect_level="low",
        user_visible_label="壞掉工具",
        requires_confirmation=False,
        permission_note="none",
    )
    monkeypatch.setitem(registry.TOOL_REGISTRY, "broken_tool", fake_tool)

    result = registry.execute_registered_tool("broken_tool", {"x": 1})
    assert result["ok"] is False
    assert result["error"]["error_code"] == "INTERNAL_ERROR"
