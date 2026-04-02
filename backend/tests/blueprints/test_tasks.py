from datetime import datetime, timedelta, timezone
from io import BytesIO

from werkzeug.security import generate_password_hash

from models import db
from models.subtask import Subtask
from models.task import Task
from models.task_comment import TaskComment
from models.task_user import TaskUser
from models.timeline import TaskFile, Timeline
from models.timeline_user import TimelineUser
from models.user import User


def _create_user(email: str, password: str, username: str) -> User:
    user = User(
        name="Task Blueprint User",
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


def _create_task(client, headers, **overrides) -> int:
    payload = {
        "name": "Task Base",
        "end_date": "2026-04-20T18:00:00",
    }
    payload.update(overrides)
    response = client.post("/api/tasks", headers=headers, json=payload)
    assert response.status_code == 201
    return response.get_json()["task_id"]


def _create_timeline(owner_id: int, name: str = "Task Timeline") -> Timeline:
    timeline = Timeline(
        user_id=owner_id,
        name=name,
        start_date=None,
        end_date=None,
        remark="",
    )
    db.session.add(timeline)
    db.session.flush()
    db.session.add(TimelineUser(timeline_id=timeline.id, user_id=owner_id, role=0))
    db.session.commit()
    return timeline


def test_get_tasks_requires_auth(client):
    response = client.get("/api/tasks")
    assert response.status_code == 401


def test_create_task_success_and_owner_membership(client):
    user = _create_user(
        email="task-create@example.com",
        password="Password123!",
        username="task_create_user",
    )
    headers = _get_auth_headers(client, "task-create@example.com", "Password123!")

    response = client.post(
        "/api/tasks",
        headers=headers,
        json={
            "name": "Implement API",
            "end_date": "2026-04-20T18:00:00",
            "priority": 1,
            "status": "pending",
        },
    )

    assert response.status_code == 201
    task_id = response.get_json()["task_id"]

    task = db.session.get(Task, task_id)
    owner_member = TaskUser.query.filter_by(task_id=task_id, user_id=user.id).first()

    assert task is not None
    assert owner_member is not None
    assert owner_member.role == 0


def test_create_task_rejects_unknown_field(client):
    _create_user(
        email="task-unknown-field@example.com",
        password="Password123!",
        username="task_unknown_field_user",
    )
    headers = _get_auth_headers(client, "task-unknown-field@example.com", "Password123!")

    response = client.post(
        "/api/tasks",
        headers=headers,
        json={
            "name": "Task with junk field",
            "end_date": "2026-04-20T18:00:00",
            "junk": True,
        },
    )

    assert response.status_code == 400


def test_create_task_invalid_status_returns_400(client):
    _create_user(
        email="task-invalid-status@example.com",
        password="Password123!",
        username="task_invalid_status_user",
    )
    headers = _get_auth_headers(client, "task-invalid-status@example.com", "Password123!")

    response = client.post(
        "/api/tasks",
        headers=headers,
        json={
            "name": "Bad status task",
            "end_date": "2026-04-20T18:00:00",
            "status": "not_a_real_status",
        },
    )

    assert response.status_code == 400


def test_create_task_priority_and_date_validations(client):
    _create_user(
        email="task-validate@example.com",
        password="Password123!",
        username="task_validate_user",
    )
    headers = _get_auth_headers(client, "task-validate@example.com", "Password123!")

    invalid_priority_type = client.post(
        "/api/tasks",
        headers=headers,
        json={
            "name": "Bad priority type",
            "end_date": "2026-04-20T18:00:00",
            "priority": "high",
        },
    )
    assert invalid_priority_type.status_code == 400

    invalid_priority_range = client.post(
        "/api/tasks",
        headers=headers,
        json={
            "name": "Bad priority range",
            "end_date": "2026-04-20T18:00:00",
            "priority": 9,
        },
    )
    assert invalid_priority_range.status_code == 400

    invalid_start_date = client.post(
        "/api/tasks",
        headers=headers,
        json={
            "name": "Bad start date",
            "start_date": "not-a-date",
            "end_date": "2026-04-20T18:00:00",
        },
    )
    assert invalid_start_date.status_code == 400

    invalid_end_date = client.post(
        "/api/tasks",
        headers=headers,
        json={
            "name": "Bad end date",
            "end_date": "not-a-date",
        },
    )
    assert invalid_end_date.status_code == 400


def test_get_tasks_returns_created_item(client):
    _create_user(
        email="task-list@example.com",
        password="Password123!",
        username="task_list_user",
    )
    headers = _get_auth_headers(client, "task-list@example.com", "Password123!")

    create_response = client.post(
        "/api/tasks",
        headers=headers,
        json={
            "name": "List me",
            "end_date": "2026-04-21T12:00:00",
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.get_json()["task_id"]

    list_response = client.get("/api/tasks", headers=headers)
    assert list_response.status_code == 200

    payload = list_response.get_json()
    assert isinstance(payload, list)
    assert any(item["task_id"] == task_id for item in payload)


def test_get_tasks_includes_assigned_task_for_member(client):
    owner = _create_user(
        email="task-owner-list@example.com",
        password="Password123!",
        username="task_owner_list_user",
    )
    member = _create_user(
        email="task-member-list@example.com",
        password="Password123!",
        username="task_member_list_user",
    )
    owner_headers = _get_auth_headers(client, "task-owner-list@example.com", "Password123!")
    member_headers = _get_auth_headers(client, "task-member-list@example.com", "Password123!")

    task_id = _create_task(client, owner_headers, name="Assigned task")
    db.session.add(TaskUser(task_id=task_id, user_id=member.id, role=1))
    db.session.commit()

    response = client.get("/api/tasks", headers=member_headers)
    assert response.status_code == 200
    payload = response.get_json()
    assigned = next(item for item in payload if item["task_id"] == task_id)
    assert assigned["is_owner"] is False


def test_update_task_success_and_validation(client):
    _create_user(
        email="task-update-success@example.com",
        password="Password123!",
        username="task_update_success_user",
    )
    headers = _get_auth_headers(client, "task-update-success@example.com", "Password123!")
    task_id = _create_task(client, headers)

    update_response = client.put(
        f"/api/tasks/{task_id}",
        headers=headers,
        json={
            "name": "Updated task name",
            "priority": 3,
            "status": "in_progress",
            "estimated_hours": 8,
            "start_date": "2026-04-01T10:00:00",
        },
    )
    assert update_response.status_code == 200

    invalid_name = client.put(
        f"/api/tasks/{task_id}",
        headers=headers,
        json={"name": "   "},
    )
    assert invalid_name.status_code == 400

    invalid_payload_type = client.put(
        f"/api/tasks/{task_id}",
        headers=headers,
        json="invalid payload",
    )
    assert invalid_payload_type.status_code == 400


def test_update_task_requires_member_role(client):
    _create_user(
        email="task-update-owner@example.com",
        password="Password123!",
        username="task_update_owner_user",
    )
    _create_user(
        email="task-update-outsider@example.com",
        password="Password123!",
        username="task_update_outsider_user",
    )

    owner_headers = _get_auth_headers(client, "task-update-owner@example.com", "Password123!")
    outsider_headers = _get_auth_headers(client, "task-update-outsider@example.com", "Password123!")
    task_id = _create_task(client, owner_headers)

    response = client.put(
        f"/api/tasks/{task_id}",
        headers=outsider_headers,
        json={"name": "should fail"},
    )
    assert response.status_code == 403


def test_toggle_task_updates_completed_and_status(client):
    _create_user(
        email="task-toggle@example.com",
        password="Password123!",
        username="task_toggle_user",
    )
    headers = _get_auth_headers(client, "task-toggle@example.com", "Password123!")
    task_id = _create_task(client, headers)

    response = client.patch(f"/api/tasks/{task_id}/toggle", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["completed"] is True

    task = db.session.get(Task, task_id)
    assert task is not None
    assert task.status == "completed"


def test_add_task_member_requires_owner(client):
    owner = _create_user(
        email="task-owner-manage@example.com",
        password="Password123!",
        username="task_owner_manage_user",
    )
    outsider = _create_user(
        email="task-outsider-manage@example.com",
        password="Password123!",
        username="task_outsider_manage_user",
    )
    target = _create_user(
        email="task-target-manage@example.com",
        password="Password123!",
        username="task_target_manage_user",
    )

    owner_headers = _get_auth_headers(client, "task-owner-manage@example.com", "Password123!")
    outsider_headers = _get_auth_headers(client, "task-outsider-manage@example.com", "Password123!")
    task_id = _create_task(client, owner_headers)

    response = client.post(
        f"/api/tasks/{task_id}/members",
        headers=outsider_headers,
        json={"user_id": target.id, "role": 1},
    )
    assert response.status_code == 403
    assert owner.id != outsider.id


def test_add_task_member_validation_duplicate_and_success(client):
    owner = _create_user(
        email="task-owner-add-member@example.com",
        password="Password123!",
        username="task_owner_add_member_user",
    )
    target = _create_user(
        email="task-target-add-member@example.com",
        password="Password123!",
        username="task_target_add_member_user",
    )
    headers = _get_auth_headers(client, "task-owner-add-member@example.com", "Password123!")
    task_id = _create_task(client, headers)

    missing_user_id = client.post(
        f"/api/tasks/{task_id}/members",
        headers=headers,
        json={},
    )
    assert missing_user_id.status_code == 400

    success = client.post(
        f"/api/tasks/{task_id}/members",
        headers=headers,
        json={"user_id": target.id, "role": 1},
    )
    assert success.status_code == 201

    duplicate = client.post(
        f"/api/tasks/{task_id}/members",
        headers=headers,
        json={"user_id": target.id, "role": 1},
    )
    assert duplicate.status_code == 409

    membership = TaskUser.query.filter_by(task_id=task_id, user_id=target.id).first()
    assert membership is not None
    assert membership.role == 1
    assert owner.id != target.id


def test_remove_task_member_owner_guard_and_success(client):
    owner = _create_user(
        email="task-owner-remove@example.com",
        password="Password123!",
        username="task_owner_remove_user",
    )
    member = _create_user(
        email="task-member-remove@example.com",
        password="Password123!",
        username="task_member_remove_user",
    )
    headers = _get_auth_headers(client, "task-owner-remove@example.com", "Password123!")
    task_id = _create_task(client, headers)
    db.session.add(TaskUser(task_id=task_id, user_id=member.id, role=1))
    db.session.commit()

    cannot_remove_owner = client.delete(
        f"/api/tasks/{task_id}/members/{owner.id}",
        headers=headers,
    )
    assert cannot_remove_owner.status_code == 400

    remove_member = client.delete(
        f"/api/tasks/{task_id}/members/{member.id}",
        headers=headers,
    )
    assert remove_member.status_code == 200
    assert TaskUser.query.filter_by(task_id=task_id, user_id=member.id).first() is None


def test_update_task_member_role_validation_and_promotion(client):
    owner = _create_user(
        email="task-owner-role@example.com",
        password="Password123!",
        username="task_owner_role_user",
    )
    timeline_member = _create_user(
        email="task-timeline-member-role@example.com",
        password="Password123!",
        username="task_timeline_member_role_user",
    )
    headers = _get_auth_headers(client, "task-owner-role@example.com", "Password123!")

    timeline = _create_timeline(owner.id, "Role Timeline")
    db.session.add(TimelineUser(timeline_id=timeline.id, user_id=timeline_member.id, role=1))
    db.session.commit()

    task_id = _create_task(client, headers, timeline_id=timeline.id)

    missing_role = client.patch(
        f"/api/tasks/{task_id}/members/{timeline_member.id}",
        headers=headers,
        json={},
    )
    assert missing_role.status_code == 400

    invalid_role = client.patch(
        f"/api/tasks/{task_id}/members/{timeline_member.id}",
        headers=headers,
        json={"role": 9},
    )
    assert invalid_role.status_code == 400

    promote = client.patch(
        f"/api/tasks/{task_id}/members/{timeline_member.id}",
        headers=headers,
        json={"role": 0},
    )
    assert promote.status_code == 200

    promoted_member = TaskUser.query.filter_by(task_id=task_id, user_id=timeline_member.id).first()
    owner_member = TaskUser.query.filter_by(task_id=task_id, user_id=owner.id).first()

    assert promoted_member is not None
    assert promoted_member.role == 0
    assert owner_member is not None
    assert owner_member.role == 1


def test_task_comment_flow_and_permissions(client):
    owner = _create_user(
        email="task-comment-owner@example.com",
        password="Password123!",
        username="task_comment_owner_user",
    )
    member = _create_user(
        email="task-comment-member@example.com",
        password="Password123!",
        username="task_comment_member_user",
    )
    owner_headers = _get_auth_headers(client, "task-comment-owner@example.com", "Password123!")
    member_headers = _get_auth_headers(client, "task-comment-member@example.com", "Password123!")

    task_id = _create_task(client, owner_headers)
    db.session.add(TaskUser(task_id=task_id, user_id=member.id, role=1))
    db.session.commit()

    add_empty = client.post(
        f"/api/tasks/{task_id}/comments",
        headers=owner_headers,
        json={"message": ""},
    )
    assert add_empty.status_code == 400

    add_response = client.post(
        f"/api/tasks/{task_id}/comments",
        headers=owner_headers,
        json={"message": "new comment"},
    )
    assert add_response.status_code == 201
    comment_id = add_response.get_json()["comment_id"]

    get_response = client.get(f"/api/tasks/{task_id}/comments", headers=member_headers)
    assert get_response.status_code == 200
    assert any(item["comment_id"] == comment_id for item in get_response.get_json())

    forbidden_delete = client.delete(
        f"/api/tasks/{task_id}/comments/{comment_id}",
        headers=member_headers,
    )
    assert forbidden_delete.status_code == 403

    own_delete = client.delete(
        f"/api/tasks/{task_id}/comments/{comment_id}",
        headers=owner_headers,
    )
    assert own_delete.status_code == 200
    comment = db.session.get(TaskComment, comment_id)
    assert comment is not None
    assert comment.deleted_at is not None
    assert owner.id != member.id


def test_ai_comment_summary_returns_empty_payload_when_no_comments(client):
    _create_user(
        email="task-summary-empty@example.com",
        password="Password123!",
        username="task_summary_empty_user",
    )
    headers = _get_auth_headers(client, "task-summary-empty@example.com", "Password123!")
    task_id = _create_task(client, headers, name="Summary empty")

    response = client.post(f"/api/tasks/{task_id}/ai-comment-summary", headers=headers, json={})
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["summary"]["decisions"] == []
    assert payload["summary"]["risks"] == []
    assert payload["summary"]["next_actions"] == []
    assert payload["meta"]["comment_count"] == 0


def test_ai_comment_summary_success(client, monkeypatch):
    import services.task_service as task_service_module

    _create_user(
        email="task-summary-success@example.com",
        password="Password123!",
        username="task_summary_success_user",
    )
    headers = _get_auth_headers(client, "task-summary-success@example.com", "Password123!")
    task_id = _create_task(client, headers, name="Summary success")

    create_comment = client.post(
        f"/api/tasks/{task_id}/comments",
        headers=headers,
        json={"message": "今天確認採用 JWT 方案"},
    )
    assert create_comment.status_code == 201

    def _fake_summary(task, comment_items):
        assert task.task_id == task_id
        assert len(comment_items) == 1
        return {
            "decisions": ["採用 JWT 驗證流程"],
            "risks": ["refresh token 失效處理需再補測"],
            "next_actions": ["補上 refresh 失效測試案例"],
        }, {
            "total_comments": 1,
            "used_comments": 1,
            "truncated": False,
            "context_chars": 120,
            "model": "qwen",
        }

    monkeypatch.setattr(task_service_module, "generate_task_comment_summary", _fake_summary)

    response = client.post(f"/api/tasks/{task_id}/ai-comment-summary", headers=headers, json={})
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["summary"]["decisions"][0] == "採用 JWT 驗證流程"
    assert payload["summary"]["risks"][0] == "refresh token 失效處理需再補測"
    assert payload["summary"]["next_actions"][0] == "補上 refresh 失效測試案例"
    assert payload["meta"]["comment_count"] == 1
    assert payload["meta"]["model"] == "qwen"


def test_ai_comment_summary_requires_member_role(client):
    _create_user(
        email="task-summary-owner@example.com",
        password="Password123!",
        username="task_summary_owner_user",
    )
    _create_user(
        email="task-summary-outsider@example.com",
        password="Password123!",
        username="task_summary_outsider_user",
    )

    owner_headers = _get_auth_headers(client, "task-summary-owner@example.com", "Password123!")
    outsider_headers = _get_auth_headers(client, "task-summary-outsider@example.com", "Password123!")
    task_id = _create_task(client, owner_headers, name="Summary role check")

    response = client.post(f"/api/tasks/{task_id}/ai-comment-summary", headers=outsider_headers, json={})
    assert response.status_code == 403


def test_ai_comment_summary_returns_503_when_service_unavailable(client, monkeypatch):
    import services.task_service as task_service_module

    _create_user(
        email="task-summary-unavailable@example.com",
        password="Password123!",
        username="task_summary_unavailable_user",
    )
    headers = _get_auth_headers(client, "task-summary-unavailable@example.com", "Password123!")
    task_id = _create_task(client, headers, name="Summary unavailable")

    create_comment = client.post(
        f"/api/tasks/{task_id}/comments",
        headers=headers,
        json={"message": "留言一"},
    )
    assert create_comment.status_code == 201

    def _fake_raise(*_args, **_kwargs):
        raise RuntimeError("AI 摘要服務暫時不可用，請稍後再試")

    monkeypatch.setattr(task_service_module, "generate_task_comment_summary", _fake_raise)

    response = client.post(f"/api/tasks/{task_id}/ai-comment-summary", headers=headers, json={})
    assert response.status_code == 503
    assert "暫時不可用" in response.get_json()["error"]


def test_task_file_upload_list_download_and_delete(client):
    owner = _create_user(
        email="task-file-owner@example.com",
        password="Password123!",
        username="task_file_owner_user",
    )
    member = _create_user(
        email="task-file-member@example.com",
        password="Password123!",
        username="task_file_member_user",
    )
    outsider = _create_user(
        email="task-file-outsider@example.com",
        password="Password123!",
        username="task_file_outsider_user",
    )

    owner_headers = _get_auth_headers(client, "task-file-owner@example.com", "Password123!")
    member_headers = _get_auth_headers(client, "task-file-member@example.com", "Password123!")
    outsider_headers = _get_auth_headers(client, "task-file-outsider@example.com", "Password123!")

    task_id = _create_task(client, owner_headers)
    db.session.add(TaskUser(task_id=task_id, user_id=member.id, role=1))
    db.session.commit()

    no_file = client.post(
        f"/api/tasks/{task_id}/upload",
        headers=owner_headers,
        data={},
        content_type="multipart/form-data",
    )
    assert no_file.status_code == 400

    unsupported = client.post(
        f"/api/tasks/{task_id}/upload",
        headers=owner_headers,
        data={"file": (BytesIO(b"bad"), "file.exe")},
        content_type="multipart/form-data",
    )
    assert unsupported.status_code == 400

    upload = client.post(
        f"/api/tasks/{task_id}/upload",
        headers=member_headers,
        data={"file": (BytesIO(b"hello"), "report.txt")},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 201
    upload_payload = upload.get_json()
    file_id = upload_payload["id"]
    stored_filename = upload_payload["filename"]

    list_response = client.get(f"/api/tasks/{task_id}/files", headers=owner_headers)
    assert list_response.status_code == 200
    assert any(item["id"] == file_id for item in list_response.get_json())

    download_unauthorized = client.get(f"/api/tasks/files/{stored_filename}")
    assert download_unauthorized.status_code == 401

    download_forbidden = client.get(
        f"/api/tasks/files/{stored_filename}",
        headers=outsider_headers,
    )
    assert download_forbidden.status_code == 403

    download = client.get(
        f"/api/tasks/files/{stored_filename}",
        headers=member_headers,
    )
    assert download.status_code == 200
    assert download.data == b"hello"
    download.close()

    forbidden_delete = client.delete(
        f"/api/tasks/{task_id}/files/{file_id}",
        headers=outsider_headers,
    )
    assert forbidden_delete.status_code == 403

    allowed_delete = client.delete(
        f"/api/tasks/{task_id}/files/{file_id}",
        headers=owner_headers,
    )
    assert allowed_delete.status_code == 200
    assert db.session.get(TaskFile, file_id) is None
    assert owner.id != outsider.id


def test_subtask_crud_flow(client):
    _create_user(
        email="task-subtask@example.com",
        password="Password123!",
        username="task_subtask_user",
    )
    headers = _get_auth_headers(client, "task-subtask@example.com", "Password123!")
    task_id = _create_task(client, headers)

    create_subtask = client.post(
        f"/api/tasks/{task_id}/subtasks",
        headers=headers,
        json={"name": "Subtask A"},
    )
    assert create_subtask.status_code == 201
    subtask_id = create_subtask.get_json()["subtask"]["id"]

    list_subtasks = client.get(f"/api/tasks/{task_id}/subtasks", headers=headers)
    assert list_subtasks.status_code == 200
    assert len(list_subtasks.get_json()) == 1

    update_subtask = client.put(
        f"/api/tasks/{task_id}/subtasks/{subtask_id}",
        headers=headers,
        json={"name": "Subtask A Updated", "completed": True, "sort_order": 3},
    )
    assert update_subtask.status_code == 200

    toggle_subtask = client.patch(
        f"/api/tasks/{task_id}/subtasks/{subtask_id}/toggle",
        headers=headers,
    )
    assert toggle_subtask.status_code == 200

    delete_subtask = client.delete(
        f"/api/tasks/{task_id}/subtasks/{subtask_id}",
        headers=headers,
    )
    assert delete_subtask.status_code == 200

    assert Subtask.query.filter_by(id=subtask_id).first() is None


def test_update_task_status_validation_and_success(client):
    _create_user(
        email="task-status@example.com",
        password="Password123!",
        username="task_status_user",
    )
    headers = _get_auth_headers(client, "task-status@example.com", "Password123!")
    task_id = _create_task(client, headers)

    invalid = client.patch(
        f"/api/tasks/{task_id}/status",
        headers=headers,
        json={"status": "bad"},
    )
    assert invalid.status_code == 400

    valid = client.patch(
        f"/api/tasks/{task_id}/status",
        headers=headers,
        json={"status": "completed"},
    )
    assert valid.status_code == 200
    assert valid.get_json()["completed"] is True


def test_get_upcoming_tasks_includes_due_and_progress_items(client):
    user = _create_user(
        email="task-upcoming@example.com",
        password="Password123!",
        username="task_upcoming_user",
    )
    headers = _get_auth_headers(client, "task-upcoming@example.com", "Password123!")
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    due_soon = Task(
        user_id=user.id,
        name="due soon",
        completed=False,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=2),
    )
    progress_warn = Task(
        user_id=user.id,
        name="progress warning",
        completed=False,
        start_date=now - timedelta(days=40),
        end_date=now + timedelta(days=10),
    )
    far_future = Task(
        user_id=user.id,
        name="not upcoming",
        completed=False,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=30),
    )
    db.session.add_all([due_soon, progress_warn, far_future])
    db.session.commit()

    response = client.get("/api/tasks/upcoming", headers=headers)
    assert response.status_code == 200

    names = {item["name"] for item in response.get_json()}
    assert "due soon" in names
    assert "progress warning" in names
    assert "not upcoming" not in names


def test_delete_task_as_owner_soft_deletes(client):
    _create_user(
        email="task-delete@example.com",
        password="Password123!",
        username="task_delete_user",
    )
    headers = _get_auth_headers(client, "task-delete@example.com", "Password123!")

    create_response = client.post(
        "/api/tasks",
        headers=headers,
        json={
            "name": "Delete me",
            "end_date": "2026-04-22T12:00:00",
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.get_json()["task_id"]

    delete_response = client.delete(f"/api/tasks/{task_id}", headers=headers)
    assert delete_response.status_code == 200

    deleted_task = db.session.get(Task, task_id)
    assert deleted_task is not None
    assert deleted_task.deleted_at is not None
