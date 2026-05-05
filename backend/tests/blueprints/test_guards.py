from blueprints.guards import require_task_role, require_timeline_role


def test_require_task_role_decorator(app, monkeypatch):
    @require_task_role("owner")
    def owner_only(task_id):
        return {"ok": True, "task_id": task_id}, 200

    with app.test_request_context("/"):
        monkeypatch.setattr("blueprints.guards.get_jwt_identity", lambda: "1")
        monkeypatch.setattr("blueprints.guards.get_user_task_role", lambda _uid, _tid: None)

        blocked = owner_only(task_id=1)
        assert blocked[1] == 403

        monkeypatch.setattr("blueprints.guards.get_user_task_role", lambda _uid, _tid: 1)
        blocked_owner = owner_only(task_id=1)
        assert blocked_owner[1] == 403

        monkeypatch.setattr("blueprints.guards.get_user_task_role", lambda _uid, _tid: 0)
        allowed = owner_only(task_id=1)
        assert allowed[1] == 200
        assert allowed[0]["ok"] is True


def test_require_timeline_role_decorator(app, monkeypatch):
    @require_timeline_role("owner")
    def owner_only(timeline_id):
        return {"ok": True, "timeline_id": timeline_id}, 200

    with app.test_request_context("/"):
        monkeypatch.setattr("blueprints.guards.get_jwt_identity", lambda: "1")
        monkeypatch.setattr("blueprints.guards.get_user_timeline_role", lambda _uid, _tid: None)

        blocked = owner_only(timeline_id=1)
        assert blocked[1] == 403

        monkeypatch.setattr("blueprints.guards.get_user_timeline_role", lambda _uid, _tid: 1)
        blocked_owner = owner_only(timeline_id=1)
        assert blocked_owner[1] == 403

        monkeypatch.setattr("blueprints.guards.get_user_timeline_role", lambda _uid, _tid: 0)
        allowed = owner_only(timeline_id=1)
        assert allowed[1] == 200
        assert allowed[0]["ok"] is True
