from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import services.timeline_service as timeline_service_module
from werkzeug.security import generate_password_hash

from models import db
from models.notification import Notification
from models.task_comment import TaskComment
from models.task import Task
from models.task_user import TaskUser
from models.timeline import Timeline
from models.timeline_user import TimelineUser
from models.user import User


def _create_user(email: str, password: str, username: str) -> User:
    user = User(
        name="Timeline Blueprint User",
        username=username,
        email=email,
        password=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()
    return user


def _get_auth_headers(client, email: str, password: str) -> dict:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_timeline(client, headers, **overrides) -> int:
    payload = {
        "name": "Roadmap",
        "start_date": "2026-04-01",
        "end_date": "2026-04-30",
        "remark": "Q2 roadmap",
    }
    payload.update(overrides)
    response = client.post("/api/timelines", headers=headers, json=payload)
    assert response.status_code == 201
    return response.get_json()["id"]


def test_get_timelines_requires_auth(client):
    response = client.get("/api/timelines")
    assert response.status_code == 401


def test_create_timeline_success_and_owner_membership(client):
    user = _create_user(
        email="timeline-create@example.com",
        password="Password123!",
        username="timeline_create_user",
    )
    headers = _get_auth_headers(client, "timeline-create@example.com", "Password123!")
    timeline_id = _create_timeline(client, headers)

    timeline = db.session.get(Timeline, timeline_id)
    owner_member = TimelineUser.query.filter_by(timeline_id=timeline_id, user_id=user.id).first()

    assert timeline is not None
    assert owner_member is not None
    assert owner_member.role == 0


def test_create_timeline_validations(client):
    _create_user(
        email="timeline-validate@example.com",
        password="Password123!",
        username="timeline_validate_user",
    )
    headers = _get_auth_headers(client, "timeline-validate@example.com", "Password123!")

    blank_name = client.post(
        "/api/timelines",
        headers=headers,
        json={"name": "   ", "start_date": "", "end_date": ""},
    )
    assert blank_name.status_code == 400

    bad_start_type = client.post(
        "/api/timelines",
        headers=headers,
        json={"name": "t1", "start_date": 1, "end_date": ""},
    )
    assert bad_start_type.status_code == 400

    bad_end_type = client.post(
        "/api/timelines",
        headers=headers,
        json={"name": "t2", "start_date": "", "end_date": 1},
    )
    assert bad_end_type.status_code == 400

    bad_date = client.post(
        "/api/timelines",
        headers=headers,
        json={"name": "t3", "start_date": "2026/01/01", "end_date": ""},
    )
    assert bad_date.status_code == 400


def test_get_timelines_returns_created_timeline(client):
    _create_user(
        email="timeline-list@example.com",
        password="Password123!",
        username="timeline_list_user",
    )
    headers = _get_auth_headers(client, "timeline-list@example.com", "Password123!")
    timeline_id = _create_timeline(
        client,
        headers,
        name="List timeline",
        start_date="2026-05-01",
        end_date="2026-05-31",
    )

    list_response = client.get("/api/timelines", headers=headers)
    assert list_response.status_code == 200

    payload = list_response.get_json()
    assert isinstance(payload, list)
    assert any(item["id"] == timeline_id for item in payload)


def test_update_timeline_unknown_field_returns_400(client):
    _create_user(
        email="timeline-update@example.com",
        password="Password123!",
        username="timeline_update_user",
    )
    headers = _get_auth_headers(client, "timeline-update@example.com", "Password123!")
    timeline_id = _create_timeline(
        client,
        headers,
        name="Update timeline",
        start_date="2026-06-01",
        end_date="2026-06-30",
    )

    update_response = client.put(
        f"/api/timelines/{timeline_id}",
        headers=headers,
        json={"not_allowed": True},
    )

    assert update_response.status_code == 400


def test_update_timeline_success_and_validation(client):
    _create_user(
        email="timeline-update-success@example.com",
        password="Password123!",
        username="timeline_update_success_user",
    )
    headers = _get_auth_headers(client, "timeline-update-success@example.com", "Password123!")
    timeline_id = _create_timeline(client, headers, name="Before Update")

    success = client.put(
        f"/api/timelines/{timeline_id}",
        headers=headers,
        json={
            "name": "After Update",
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
            "remark": "updated",
        },
    )
    assert success.status_code == 200

    invalid_name = client.put(
        f"/api/timelines/{timeline_id}",
        headers=headers,
        json={"name": "  "},
    )
    assert invalid_name.status_code == 400

    invalid_date = client.put(
        f"/api/timelines/{timeline_id}",
        headers=headers,
        json={"end_date": "not-a-date"},
    )
    assert invalid_date.status_code == 400


def test_delete_timeline_soft_deletes_timeline_and_related_tasks(client):
    user = _create_user(
        email="timeline-delete@example.com",
        password="Password123!",
        username="timeline_delete_user",
    )
    headers = _get_auth_headers(client, "timeline-delete@example.com", "Password123!")
    timeline_id = _create_timeline(
        client,
        headers,
        name="Delete timeline",
        start_date="2026-07-01",
        end_date="2026-07-31",
    )

    task = Task(
        user_id=user.id,
        timeline_id=timeline_id,
        name="Timeline task",
    )
    db.session.add(task)
    db.session.commit()
    task_id = task.task_id

    delete_response = client.delete(f"/api/timelines/{timeline_id}", headers=headers)
    assert delete_response.status_code == 200

    deleted_timeline = db.session.get(Timeline, timeline_id)
    deleted_task = db.session.get(Task, task_id)

    assert deleted_timeline is not None
    assert deleted_timeline.deleted_at is not None
    assert deleted_task is not None
    assert deleted_task.deleted_at is not None


def test_get_timeline_tasks_and_remark_update(client):
    owner = _create_user(
        email="timeline-task-owner@example.com",
        password="Password123!",
        username="timeline_task_owner_user",
    )
    assistant = _create_user(
        email="timeline-task-assistant@example.com",
        password="Password123!",
        username="timeline_task_assistant_user",
    )
    headers = _get_auth_headers(client, "timeline-task-owner@example.com", "Password123!")
    timeline_id = _create_timeline(client, headers, name="Task detail timeline")

    task = Task(
        user_id=owner.id,
        timeline_id=timeline_id,
        name="Timeline task with members",
        status="in_progress",
    )
    db.session.add(task)
    db.session.flush()
    db.session.add(TaskUser(task_id=task.task_id, user_id=owner.id, role=0))
    db.session.add(TaskUser(task_id=task.task_id, user_id=assistant.id, role=1))
    db.session.commit()

    tasks_response = client.get(f"/api/timelines/{timeline_id}/tasks", headers=headers)
    assert tasks_response.status_code == 200
    payload = tasks_response.get_json()
    assert len(payload) == 1
    assert payload[0]["assignee"] == owner.name
    assert assistant.name in payload[0]["assistant"]
    assert payload[0]["can_manage_members"] is True

    invalid_remark = client.put(
        f"/api/timelines/{timeline_id}/remark",
        headers=headers,
        json={"remark": 123},
    )
    assert invalid_remark.status_code == 400

    valid_remark = client.put(
        f"/api/timelines/{timeline_id}/remark",
        headers=headers,
        json={"remark": "remark updated"},
    )
    assert valid_remark.status_code == 200


def test_get_timeline_tasks_can_manage_members_for_task_owner_member(client):
    timeline_owner = _create_user(
        email="timeline-manage-owner@example.com",
        password="Password123!",
        username="timeline_manage_owner",
    )
    collaborator = _create_user(
        email="timeline-manage-collaborator@example.com",
        password="Password123!",
        username="timeline_manage_collaborator",
    )

    owner_headers = _get_auth_headers(client, "timeline-manage-owner@example.com", "Password123!")
    collaborator_headers = _get_auth_headers(client, "timeline-manage-collaborator@example.com", "Password123!")
    timeline_id = _create_timeline(client, owner_headers, name="Task manage permission timeline")

    db.session.add(TimelineUser(timeline_id=timeline_id, user_id=collaborator.id, role=1))

    task_owned_by_collaborator = Task(
        user_id=collaborator.id,
        timeline_id=timeline_id,
        name="Collaborator owned task",
    )
    task_only_collaborator = Task(
        user_id=timeline_owner.id,
        timeline_id=timeline_id,
        name="Collaborator non-owner task",
    )
    db.session.add_all([task_owned_by_collaborator, task_only_collaborator])
    db.session.flush()

    db.session.add_all(
        [
            TaskUser(task_id=task_owned_by_collaborator.task_id, user_id=collaborator.id, role=0),
            TaskUser(task_id=task_only_collaborator.task_id, user_id=timeline_owner.id, role=0),
            TaskUser(task_id=task_only_collaborator.task_id, user_id=collaborator.id, role=1),
        ]
    )
    db.session.commit()

    response = client.get(f"/api/timelines/{timeline_id}/tasks", headers=collaborator_headers)
    assert response.status_code == 200

    payload = response.get_json()
    manage_map = {item["name"]: item["can_manage_members"] for item in payload}
    assert manage_map["Collaborator owned task"] is True
    assert manage_map["Collaborator non-owner task"] is False


def test_search_user_by_email_flow(client):
    _create_user(
        email="timeline-search@example.com",
        password="Password123!",
        username="timeline_search_user",
    )
    _create_user(
        email="timeline-search-target@example.com",
        password="Password123!",
        username="timeline_search_target_user",
    )

    headers = _get_auth_headers(client, "timeline-search@example.com", "Password123!")

    missing_email = client.post(
        "/api/timelines/search_user",
        headers=headers,
        json={},
    )
    assert missing_email.status_code == 400

    not_found = client.post(
        "/api/timelines/search_user",
        headers=headers,
        json={"email": "noone@example.com"},
    )
    assert not_found.status_code == 404

    found = client.post(
        "/api/timelines/search_user",
        headers=headers,
        json={"email": "timeline-search-target@example.com"},
    )
    assert found.status_code == 200
    assert found.get_json()["email"] == "timeline-search-target@example.com"


def test_timeline_members_add_get_remove_and_notification(client):
    owner = _create_user(
        email="timeline-member-owner@example.com",
        password="Password123!",
        username="timeline_member_owner_user",
    )
    invited = _create_user(
        email="timeline-member-invited@example.com",
        password="Password123!",
        username="timeline_member_invited_user",
    )
    headers = _get_auth_headers(client, "timeline-member-owner@example.com", "Password123!")
    timeline_id = _create_timeline(client, headers, name="Member timeline")

    add_member = client.post(
        f"/api/timelines/{timeline_id}/members",
        headers=headers,
        json={"user_id": invited.id, "role": 1},
    )
    assert add_member.status_code == 201

    notif = Notification.query.filter_by(user_id=invited.id, type="timeline_invited").first()
    assert notif is not None

    members = client.get(f"/api/timelines/{timeline_id}/members", headers=headers)
    assert members.status_code == 200
    member_ids = {item["user_id"] for item in members.get_json()}
    assert owner.id in member_ids
    assert invited.id in member_ids

    remove_member = client.delete(
        f"/api/timelines/{timeline_id}/members/{invited.id}",
        headers=headers,
    )
    assert remove_member.status_code == 200


def test_remove_timeline_member_self_and_owner_permission_guards(client):
    owner = _create_user(
        email="timeline-guard-owner@example.com",
        password="Password123!",
        username="timeline_guard_owner_user",
    )
    collaborator = _create_user(
        email="timeline-guard-collab@example.com",
        password="Password123!",
        username="timeline_guard_collab_user",
    )
    target = _create_user(
        email="timeline-guard-target@example.com",
        password="Password123!",
        username="timeline_guard_target_user",
    )

    owner_headers = _get_auth_headers(client, "timeline-guard-owner@example.com", "Password123!")
    collab_headers = _get_auth_headers(client, "timeline-guard-collab@example.com", "Password123!")
    timeline_id = _create_timeline(client, owner_headers, name="Guard timeline")

    db.session.add(TimelineUser(timeline_id=timeline_id, user_id=collaborator.id, role=1))
    db.session.add(TimelineUser(timeline_id=timeline_id, user_id=target.id, role=1))
    db.session.commit()

    remove_self = client.delete(
        f"/api/timelines/{timeline_id}/members/{owner.id}",
        headers=owner_headers,
    )
    assert remove_self.status_code == 400

    collab_remove = client.delete(
        f"/api/timelines/{timeline_id}/members/{target.id}",
        headers=collab_headers,
    )
    assert collab_remove.status_code == 403


def test_generate_tasks_with_ai_guards(client, monkeypatch):
    _create_user(
        email="timeline-ai-guard@example.com",
        password="Password123!",
        username="timeline_ai_guard_user",
    )
    headers = _get_auth_headers(client, "timeline-ai-guard@example.com", "Password123!")
    timeline_id = _create_timeline(client, headers, name="AI guard timeline")

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    missing_key = client.post(
        f"/api/timelines/{timeline_id}/generate-tasks",
        headers=headers,
        json={"name": "AI project"},
    )
    assert missing_key.status_code == 500

    blank_name = client.post(
        f"/api/timelines/{timeline_id}/generate-tasks",
        headers=headers,
        json={"name": "  "},
    )
    assert blank_name.status_code == 400


def test_generate_tasks_with_ai_success_and_json_decode_error(client, monkeypatch):
    owner = _create_user(
        email="timeline-ai-success@example.com",
        password="Password123!",
        username="timeline_ai_success_user",
    )
    headers = _get_auth_headers(client, "timeline-ai-success@example.com", "Password123!")
    timeline_id = _create_timeline(client, headers, name="AI success timeline")

    existing_task = Task(
        user_id=owner.id,
        timeline_id=timeline_id,
        name="Existing task",
        start_date=datetime(2026, 4, 1),
        end_date=datetime(2026, 4, 4),
    )
    db.session.add(existing_task)
    db.session.commit()

    # 模擬 LangChain 成功回傳 timeline 任務生成結果
    from unittest.mock import MagicMock
    mock_llm = MagicMock()
    mock_generate_tasks = MagicMock(return_value=[
        {"name": "AI Task", "priority": 1, "estimated_days": 2, "task_remark": "AI generated"}
    ])

    monkeypatch.setattr(timeline_service_module, "get_default_llm", MagicMock(return_value=mock_llm))
    monkeypatch.setattr(timeline_service_module, "generate_timeline_tasks_from_context", mock_generate_tasks)

    success = client.post(
        f"/api/timelines/{timeline_id}/generate-tasks",
        headers=headers,
        json={"name": "AI Project", "description": "Generate tasks"},
    )
    assert success.status_code == 200
    payload = success.get_json()
    assert payload["existingCount"] == 1
    assert payload["generatedCount"] == 1
    assert len(payload["tasks"]) == 2

    # 模擬鏈路輔助函式拋出 ValueError（LLM JSON 無效）
    mock_generate_tasks_error = MagicMock(side_effect=ValueError("Invalid JSON from LLM"))
    monkeypatch.setattr(timeline_service_module, "generate_timeline_tasks_from_context", mock_generate_tasks_error)

    bad_json = client.post(
        f"/api/timelines/{timeline_id}/generate-tasks",
        headers=headers,
        json={"name": "AI Project", "description": "Generate tasks"},
    )
    assert bad_json.status_code == 500


def test_batch_create_tasks_validation_and_success(client):
    owner = _create_user(
        email="timeline-batch-owner@example.com",
        password="Password123!",
        username="timeline_batch_owner_user",
    )
    headers = _get_auth_headers(client, "timeline-batch-owner@example.com", "Password123!")
    timeline_id = _create_timeline(client, headers, name="Batch timeline", start_date="", end_date="")

    keep_task = Task(user_id=owner.id, timeline_id=timeline_id, name="keep me")
    delete_task = Task(user_id=owner.id, timeline_id=timeline_id, name="delete me")
    db.session.add_all([keep_task, delete_task])
    db.session.commit()

    invalid_payload = client.post(
        f"/api/timelines/{timeline_id}/batch-create-tasks",
        headers=headers,
        json={"tasks": []},
    )
    assert invalid_payload.status_code == 400

    response = client.post(
        f"/api/timelines/{timeline_id}/batch-create-tasks",
        headers=headers,
        json={
            "tasks": [
                {"task_id": keep_task.task_id, "isExisting": True, "name": "keep me"},
                {
                    "isExisting": False,
                    "name": "new ai task",
                    "priority": 1,
                    "status": "pending",
                    "estimated_days": 2,
                    "task_remark": "created",
                    "depends_on_task_ids": [keep_task.task_id],
                    "depends_on_task_refs": ["keep me", "不存在任務"],
                },
            ]
        },
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["kept"] == 1
    assert payload["deleted"] == 1
    assert payload["created"] == 1
    assert payload["ignored_dependency_refs"] == 1

    refreshed_keep = db.session.get(Task, keep_task.task_id)
    refreshed_delete = db.session.get(Task, delete_task.task_id)
    new_task = Task.query.filter_by(timeline_id=timeline_id, name="new ai task").first()

    assert refreshed_keep is not None
    assert refreshed_keep.deleted_at is None
    assert refreshed_delete is not None
    assert refreshed_delete.deleted_at is not None
    assert new_task is not None
    assert new_task.depends_on_task_ids == [keep_task.task_id]


def test_batch_create_tasks_partial_selection_keeps_resolvable_dependencies(client):
    owner = _create_user(
        email="timeline-batch-partial-owner@example.com",
        password="Password123!",
        username="timeline_batch_partial_owner",
    )
    headers = _get_auth_headers(client, "timeline-batch-partial-owner@example.com", "Password123!")
    timeline_id = _create_timeline(client, headers, name="Batch partial chain timeline", start_date="", end_date="")

    response = client.post(
        f"/api/timelines/{timeline_id}/batch-create-tasks",
        headers=headers,
        json={
            "tasks": [
                {
                    "isExisting": False,
                    "name": "任務1",
                    "priority": 2,
                    "status": "pending",
                    "estimated_days": 1,
                    "task_remark": "chain 1",
                    "depends_on_task_refs": [],
                },
                {
                    "isExisting": False,
                    "name": "任務2",
                    "priority": 2,
                    "status": "pending",
                    "estimated_days": 1,
                    "task_remark": "chain 2",
                    "depends_on_task_refs": ["任務1"],
                },
                {
                    "isExisting": False,
                    "name": "任務4",
                    "priority": 2,
                    "status": "pending",
                    "estimated_days": 1,
                    "task_remark": "chain 4",
                    "depends_on_task_refs": ["任務3"],
                },
                {
                    "isExisting": False,
                    "name": "任務5",
                    "priority": 2,
                    "status": "pending",
                    "estimated_days": 1,
                    "task_remark": "chain 5",
                    "depends_on_task_refs": ["任務4"],
                },
            ]
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["created"] == 4
    assert payload["ignored_dependency_refs"] == 1

    task_1 = Task.query.filter_by(timeline_id=timeline_id, name="任務1").first()
    task_2 = Task.query.filter_by(timeline_id=timeline_id, name="任務2").first()
    task_4 = Task.query.filter_by(timeline_id=timeline_id, name="任務4").first()
    task_5 = Task.query.filter_by(timeline_id=timeline_id, name="任務5").first()

    assert task_1 is not None
    assert task_2 is not None
    assert task_4 is not None
    assert task_5 is not None

    # 可解析依賴要保留（任務2 -> 任務1、任務5 -> 任務4）
    assert task_1.depends_on_task_ids == []
    assert task_2.depends_on_task_ids == [task_1.task_id]
    assert task_5.depends_on_task_ids == [task_4.task_id]

    # 缺失前置依賴（任務4 -> 任務3）應降級為無依賴，不阻塞建立
    assert task_4.depends_on_task_ids == []


def test_get_timeline_weekly_report_returns_completed_and_risk_items(client):
    owner = _create_user(
        email="timeline-weekly-api-owner@example.com",
        password="Password123!",
        username="timeline_weekly_api_owner",
    )
    member = _create_user(
        email="timeline-weekly-api-member@example.com",
        password="Password123!",
        username="timeline_weekly_api_member",
    )

    headers = _get_auth_headers(client, "timeline-weekly-api-owner@example.com", "Password123!")
    timeline_id = _create_timeline(client, headers, name="Weekly API Timeline")

    db.session.add(TimelineUser(timeline_id=timeline_id, user_id=member.id, role=1))
    completed_task = Task(
        user_id=owner.id,
        timeline_id=timeline_id,
        name="本期完成",
        completed=True,
        status="completed",
        end_date=datetime(2026, 4, 15),
        completed_at=datetime(2026, 4, 15, 9, 0, 0),
    )
    risk_task = Task(
        user_id=member.id,
        timeline_id=timeline_id,
        name="本期風險",
        completed=False,
        status="in_progress",
        end_date=datetime(2026, 4, 16),
    )
    db.session.add_all([completed_task, risk_task])
    db.session.flush()
    db.session.add(
        TaskComment(
            task_id=risk_task.task_id,
            user_id=member.id,
            task_message="等待後端 schema 更新",
            created_at=datetime(2026, 4, 16, 11, 0, 0),
        )
    )
    db.session.commit()

    response = client.get(
        f"/api/timelines/{timeline_id}/weekly-report?start_date=2026-04-14&end_date=2026-04-20",
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.get_json()

    assert payload["timeline_id"] == timeline_id
    assert payload["overview"]["completed_tasks"] == 1
    assert payload["overview"]["at_risk_tasks"] == 1
    assert payload["overview"]["comment_count"] == 1
    assert any(item["name"] == "本期完成" for item in payload["completed_tasks"])
    assert any(item["name"] == "本期風險" for item in payload["risk_items"])
    assert payload["analysis"]["weekly_goal_total"] == 2
    assert payload["analysis"]["weekly_goal_completed"] == 1
    assert payload["analysis"]["progress_signal"] in {"進度領先", "進度穩定", "進度落後"}


def test_get_timeline_risk_analysis_returns_summary_and_warnings(client):
    owner = _create_user(
        email="timeline-risk-api-owner@example.com",
        password="Password123!",
        username="timeline_risk_api_owner",
    )

    headers = _get_auth_headers(client, "timeline-risk-api-owner@example.com", "Password123!")
    timeline_id = _create_timeline(client, headers, name="Risk API Timeline")

    task_a = Task(
        user_id=owner.id,
        timeline_id=timeline_id,
        name="風險任務 A",
        start_date=datetime(2026, 4, 10),
        end_date=datetime(2026, 4, 11),
        completed=False,
    )
    task_b = Task(
        user_id=owner.id,
        timeline_id=timeline_id,
        name="風險任務 B",
        start_date=datetime(2026, 4, 12),
        end_date=datetime(2026, 4, 13),
        completed=False,
    )
    db.session.add_all([task_a, task_b])
    db.session.flush()
    task_b.depends_on_task_ids = [task_a.task_id, 999999]
    db.session.commit()

    response = client.get(f"/api/timelines/{timeline_id}/risk-analysis", headers=headers)
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["timeline_id"] == timeline_id
    assert payload["summary"]["total_tasks"] == 2
    assert "critical_path" in payload
    assert "risk_items" in payload
    assert "warnings" in payload

    warning_codes = {item["code"] for item in payload["warnings"]}
    assert "missing_dependency" in warning_codes


def test_post_timeline_risk_analysis_notify_owner_only(client):
    owner = _create_user(
        email="timeline-risk-notify-api-owner@example.com",
        password="Password123!",
        username="timeline_risk_notify_api_owner",
    )
    member = _create_user(
        email="timeline-risk-notify-api-member@example.com",
        password="Password123!",
        username="timeline_risk_notify_api_member",
    )

    owner_headers = _get_auth_headers(client, "timeline-risk-notify-api-owner@example.com", "Password123!")
    member_headers = _get_auth_headers(client, "timeline-risk-notify-api-member@example.com", "Password123!")
    timeline_id = _create_timeline(client, owner_headers, name="Risk Notify API Timeline")

    db.session.add(TimelineUser(timeline_id=timeline_id, user_id=member.id, role=1))

    blocker = Task(
        user_id=owner.id,
        timeline_id=timeline_id,
        name="關鍵阻塞任務",
        start_date=datetime(2026, 4, 10),
        end_date=datetime(2026, 4, 11),
        status="in_progress",
        completed=False,
    )
    follower = Task(
        user_id=member.id,
        timeline_id=timeline_id,
        name="後續驗收",
        start_date=datetime(2026, 4, 12),
        end_date=datetime(2026, 4, 13),
        status="pending",
        completed=False,
    )
    db.session.add_all([blocker, follower])
    db.session.flush()
    follower.depends_on_task_ids = [blocker.task_id]
    db.session.commit()

    forbidden = client.post(f"/api/timelines/{timeline_id}/risk-analysis/notify", headers=member_headers)
    assert forbidden.status_code == 403

    allowed = client.post(f"/api/timelines/{timeline_id}/risk-analysis/notify", headers=owner_headers)
    assert allowed.status_code == 200

    payload = allowed.get_json()
    assert payload["timeline_id"] == timeline_id
    assert payload["notified_user_count"] >= 1


def test_timeline_conflict_check_api_detects_overlap_and_validates_payload(client):
    owner = _create_user(
        email="timeline-conflict-api-owner@example.com",
        password="Password123!",
        username="timeline_conflict_api_owner",
    )
    headers = _get_auth_headers(client, "timeline-conflict-api-owner@example.com", "Password123!")
    timeline_id = _create_timeline(client, headers, name="Conflict API Timeline")

    existing_task = Task(
        user_id=owner.id,
        timeline_id=timeline_id,
        name="既有排程",
        status="in_progress",
        start_date=datetime(2026, 4, 10),
        end_date=datetime(2026, 4, 12),
    )
    db.session.add(existing_task)
    db.session.flush()
    db.session.add(TaskUser(task_id=existing_task.task_id, user_id=owner.id, role=0))
    db.session.commit()

    conflict_response = client.post(
        f"/api/timelines/{timeline_id}/conflict-check",
        headers=headers,
        json={
            "name": "新任務",
            "start_date": "2026-04-11",
            "end_date": "2026-04-13",
        },
    )
    assert conflict_response.status_code == 200

    payload = conflict_response.get_json()
    assert payload["has_conflict"] is True
    assert payload["conflict_count"] >= 1
    assert payload["conflicts"][0]["task_id"] == existing_task.task_id
    assert payload["suggestion"]["start_date"] == "2026-04-13"
    assert payload["cross_project_conflict_count"] == 0
    assert payload["workload_overload_count"] == 0
    assert payload["workload_overload_days"] == []

    invalid_response = client.post(
        f"/api/timelines/{timeline_id}/conflict-check",
        headers=headers,
        json={"name": "缺少日期"},
    )
    assert invalid_response.status_code == 400

    outsider = _create_user(
        email="timeline-conflict-api-outsider@example.com",
        password="Password123!",
        username="timeline_conflict_api_outsider",
    )
    non_member_assignee_response = client.post(
        f"/api/timelines/{timeline_id}/conflict-check",
        headers=headers,
        json={
            "name": "外部指派",
            "start_date": "2026-04-11",
            "end_date": "2026-04-13",
            "assignee_user_id": outsider.id,
        },
    )
    assert non_member_assignee_response.status_code == 400


def test_get_upcoming_timelines_returns_due_and_progress_items(client):
    owner = _create_user(
        email="timeline-upcoming-owner@example.com",
        password="Password123!",
        username="timeline_upcoming_owner_user",
    )
    headers = _get_auth_headers(client, "timeline-upcoming-owner@example.com", "Password123!")

    today = datetime.now(timezone.utc).date()
    due_timeline = Timeline(
        user_id=owner.id,
        name="due timeline",
        start_date=today - timedelta(days=2),
        end_date=today + timedelta(days=2),
        remark="",
    )
    progress_timeline = Timeline(
        user_id=owner.id,
        name="progress timeline",
        start_date=today - timedelta(days=40),
        end_date=today + timedelta(days=5),
        remark="",
    )
    far_timeline = Timeline(
        user_id=owner.id,
        name="far timeline",
        start_date=today,
        end_date=today + timedelta(days=30),
        remark="",
    )
    db.session.add_all([due_timeline, progress_timeline, far_timeline])
    db.session.flush()
    db.session.add_all(
        [
            TimelineUser(timeline_id=due_timeline.id, user_id=owner.id, role=0),
            TimelineUser(timeline_id=progress_timeline.id, user_id=owner.id, role=0),
            TimelineUser(timeline_id=far_timeline.id, user_id=owner.id, role=0),
        ]
    )
    db.session.commit()

    response = client.get("/api/timelines/upcoming", headers=headers)
    assert response.status_code == 200
    names = {item["name"] for item in response.get_json()}
    assert "due timeline" in names
    assert "progress timeline" in names
    assert "far timeline" not in names


def test_get_member_stats_owner_only_and_payload(client):
    owner = _create_user(
        email="timeline-stats-owner@example.com",
        password="Password123!",
        username="timeline_stats_owner_user",
    )
    member = _create_user(
        email="timeline-stats-member@example.com",
        password="Password123!",
        username="timeline_stats_member_user",
    )

    owner_headers = _get_auth_headers(client, "timeline-stats-owner@example.com", "Password123!")
    member_headers = _get_auth_headers(client, "timeline-stats-member@example.com", "Password123!")
    timeline_id = _create_timeline(client, owner_headers, name="Stats timeline")

    db.session.add(TimelineUser(timeline_id=timeline_id, user_id=member.id, role=1))
    db.session.flush()

    task_1 = Task(
        user_id=owner.id,
        timeline_id=timeline_id,
        name="owner task",
        completed=True,
        status="completed",
    )
    task_2 = Task(
        user_id=member.id,
        timeline_id=timeline_id,
        name="member task",
        completed=False,
        status="in_progress",
    )
    db.session.add_all([task_1, task_2])
    db.session.flush()
    db.session.add(TaskUser(task_id=task_1.task_id, user_id=member.id, role=1))
    db.session.commit()

    forbidden = client.get(f"/api/timelines/{timeline_id}/member-stats", headers=member_headers)
    assert forbidden.status_code == 403

    allowed = client.get(f"/api/timelines/{timeline_id}/member-stats", headers=owner_headers)
    assert allowed.status_code == 200
    payload = allowed.get_json()

    assert payload["total_tasks"] == 2
    assert payload["status_distribution"]["completed"] == 1
    assert payload["status_distribution"]["in_progress"] == 1
    assert len(payload["members"]) == 2
