from datetime import datetime, timedelta, timezone
from io import BytesIO


from models import db
from models.task import Task
from models.task_user import TaskUser
from models.user import User



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


def test_get_tasks_requires_auth(client, auth_user_factory):
    response = client.get("/api/tasks")
    assert response.status_code == 401


def test_create_task_endpoint_returns_task_id_and_owner_membership(client, auth_user_factory):
    user = auth_user_factory(
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
    assert db.session.get(Task, task_id) is not None

    owner_member = TaskUser.query.filter_by(task_id=task_id, user_id=user.id).first()
    assert owner_member is not None
    assert owner_member.role == 0


def test_create_task_endpoint_maps_validation_errors(client, auth_user_factory):
    auth_user_factory(
        email="task-validation-map@example.com",
        password="Password123!",
        username="task_validation_map_user",
    )
    headers = _get_auth_headers(client, "task-validation-map@example.com", "Password123!")

    invalid_json = client.post("/api/tasks", headers=headers, json="invalid payload")
    assert invalid_json.status_code == 400

    service_error = client.post(
        "/api/tasks",
        headers=headers,
        json={
            "name": "Bad status task",
            "end_date": "2026-04-20T18:00:00",
            "status": "not_a_real_status",
        },
    )
    assert service_error.status_code == 400

    unknown_field = client.post(
        "/api/tasks",
        headers=headers,
        json={
            "name": "Task with junk field",
            "end_date": "2026-04-20T18:00:00",
            "junk": True,
        },
    )
    assert unknown_field.status_code == 400

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


def test_get_tasks_endpoint_returns_created_item(client, auth_user_factory):
    auth_user_factory(
        email="task-list@example.com",
        password="Password123!",
        username="task_list_user",
    )
    headers = _get_auth_headers(client, "task-list@example.com", "Password123!")
    task_id = _create_task(client, headers, name="List me")

    response = client.get("/api/tasks", headers=headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, list)
    assert any(item["task_id"] == task_id for item in payload)


def test_update_task_endpoint_maps_success_and_guards(client, auth_user_factory):
    auth_user_factory(
        email="task-update-owner@example.com",
        password="Password123!",
        username="task_update_owner_user",
    )
    auth_user_factory(
        email="task-update-outsider@example.com",
        password="Password123!",
        username="task_update_outsider_user",
    )

    owner_headers = _get_auth_headers(client, "task-update-owner@example.com", "Password123!")
    outsider_headers = _get_auth_headers(client, "task-update-outsider@example.com", "Password123!")
    task_id = _create_task(client, owner_headers)

    success = client.put(
        f"/api/tasks/{task_id}",
        headers=owner_headers,
        json={"name": "Updated task name", "status": "in_progress"},
    )
    assert success.status_code == 200

    invalid_payload_type = client.put(
        f"/api/tasks/{task_id}",
        headers=owner_headers,
        json="invalid payload",
    )
    assert invalid_payload_type.status_code == 400

    invalid_name = client.put(
        f"/api/tasks/{task_id}",
        headers=owner_headers,
        json={"name": "   "},
    )
    assert invalid_name.status_code == 400

    invalid_status = client.put(
        f"/api/tasks/{task_id}",
        headers=owner_headers,
        json={"status": "not_a_real_status"},
    )
    assert invalid_status.status_code == 400

    forbidden = client.put(
        f"/api/tasks/{task_id}",
        headers=outsider_headers,
        json={"name": "should fail"},
    )
    assert forbidden.status_code == 403


def test_task_member_endpoints_map_service_results(client, auth_user_factory):
    auth_user_factory(
        email="task-member-owner@example.com",
        password="Password123!",
        username="task_member_owner_user",
    )
    target = auth_user_factory(
        email="task-member-target@example.com",
        password="Password123!",
        username="task_member_target_user",
    )
    auth_user_factory(
        email="task-member-outsider@example.com",
        password="Password123!",
        username="task_member_outsider_user",
    )
    headers = _get_auth_headers(client, "task-member-owner@example.com", "Password123!")
    outsider_headers = _get_auth_headers(client, "task-member-outsider@example.com", "Password123!")
    task_id = _create_task(client, headers)

    missing_user_id = client.post(
        f"/api/tasks/{task_id}/members",
        headers=headers,
        json={},
    )
    assert missing_user_id.status_code == 400

    add_member = client.post(
        f"/api/tasks/{task_id}/members",
        headers=headers,
        json={"user_id": target.id, "role": 1},
    )
    assert add_member.status_code == 201

    duplicate_member = client.post(
        f"/api/tasks/{task_id}/members",
        headers=headers,
        json={"user_id": target.id, "role": 1},
    )
    assert duplicate_member.status_code == 409

    forbidden_add = client.post(
        f"/api/tasks/{task_id}/members",
        headers=outsider_headers,
        json={"user_id": target.id, "role": 1},
    )
    assert forbidden_add.status_code == 403

    list_members = client.get(f"/api/tasks/{task_id}/members", headers=headers)
    assert list_members.status_code == 200
    assert any(item["user_id"] == target.id for item in list_members.get_json())

    remove_member = client.delete(
        f"/api/tasks/{task_id}/members/{target.id}",
        headers=headers,
    )
    assert remove_member.status_code == 200


def test_task_member_role_endpoint_validations_and_permissions(client, auth_user_factory):
    auth_user_factory(
        email="task-member-role-owner@example.com",
        password="Password123!",
        username="task_member_role_owner_user",
    )
    member = auth_user_factory(
        email="task-member-role-member@example.com",
        password="Password123!",
        username="task_member_role_member_user",
    )
    auth_user_factory(
        email="task-member-role-outsider@example.com",
        password="Password123!",
        username="task_member_role_outsider_user",
    )
    owner_headers = _get_auth_headers(client, "task-member-role-owner@example.com", "Password123!")
    outsider_headers = _get_auth_headers(client, "task-member-role-outsider@example.com", "Password123!")
    task_id = _create_task(client, owner_headers)

    add_member = client.post(
        f"/api/tasks/{task_id}/members",
        headers=owner_headers,
        json={"user_id": member.id, "role": 1},
    )
    assert add_member.status_code == 201

    missing_role = client.patch(
        f"/api/tasks/{task_id}/members/{member.id}",
        headers=owner_headers,
        json={},
    )
    assert missing_role.status_code == 400

    invalid_type = client.patch(
        f"/api/tasks/{task_id}/members/{member.id}",
        headers=owner_headers,
        json={"role": "bad"},
    )
    assert invalid_type.status_code == 400

    invalid_value = client.patch(
        f"/api/tasks/{task_id}/members/{member.id}",
        headers=owner_headers,
        json={"role": 9},
    )
    assert invalid_value.status_code == 400

    forbidden = client.patch(
        f"/api/tasks/{task_id}/members/{member.id}",
        headers=outsider_headers,
        json={"role": 0},
    )
    assert forbidden.status_code == 403

    promote = client.patch(
        f"/api/tasks/{task_id}/members/{member.id}",
        headers=owner_headers,
        json={"role": 0},
    )
    assert promote.status_code == 200


def test_task_comment_endpoints_map_crud_flow(client, auth_user_factory):
    auth_user_factory(
        email="task-comment-owner@example.com",
        password="Password123!",
        username="task_comment_owner_user",
    )
    headers = _get_auth_headers(client, "task-comment-owner@example.com", "Password123!")
    task_id = _create_task(client, headers)

    add_response = client.post(
        f"/api/tasks/{task_id}/comments",
        headers=headers,
        json={"message": "new comment"},
    )
    assert add_response.status_code == 201
    comment_id = add_response.get_json()["comment_id"]

    get_response = client.get(f"/api/tasks/{task_id}/comments", headers=headers)
    assert get_response.status_code == 200
    assert any(item["comment_id"] == comment_id for item in get_response.get_json())

    delete_response = client.delete(
        f"/api/tasks/{task_id}/comments/{comment_id}",
        headers=headers,
    )
    assert delete_response.status_code == 200


def test_task_comment_endpoints_reject_invalid_and_forbidden(client, auth_user_factory):
    auth_user_factory(
        email="task-comment-owner2@example.com",
        password="Password123!",
        username="task_comment_owner_user2",
    )
    auth_user_factory(
        email="task-comment-outsider@example.com",
        password="Password123!",
        username="task_comment_outsider_user",
    )
    owner_headers = _get_auth_headers(client, "task-comment-owner2@example.com", "Password123!")
    outsider_headers = _get_auth_headers(client, "task-comment-outsider@example.com", "Password123!")
    task_id = _create_task(client, owner_headers)

    empty_message = client.post(
        f"/api/tasks/{task_id}/comments",
        headers=owner_headers,
        json={"message": ""},
    )
    assert empty_message.status_code == 400

    forbidden_add = client.post(
        f"/api/tasks/{task_id}/comments",
        headers=outsider_headers,
        json={"message": "should fail"},
    )
    assert forbidden_add.status_code == 403

    add_response = client.post(
        f"/api/tasks/{task_id}/comments",
        headers=owner_headers,
        json={"message": "comment"},
    )
    assert add_response.status_code == 201
    comment_id = add_response.get_json()["comment_id"]

    forbidden_delete = client.delete(
        f"/api/tasks/{task_id}/comments/{comment_id}",
        headers=outsider_headers,
    )
    assert forbidden_delete.status_code == 403


def test_ai_comment_summary_endpoint_maps_service_payload_and_errors(client, monkeypatch, auth_user_factory):
    auth_user_factory(
        email="task-summary-route@example.com",
        password="Password123!",
        username="task_summary_route_user",
    )
    headers = _get_auth_headers(client, "task-summary-route@example.com", "Password123!")
    task_id = _create_task(client, headers, name="Summary route")

    def _fake_summary(_task_id):
        return {
            "task_id": task_id,
            "summary": {
                "decisions": ["adopt JWT"],
                "risks": [],
                "next_actions": [],
            },
            "meta": {"comment_count": 1, "model": "test-model"},
        }

    monkeypatch.setattr("blueprints.tasks.summarize_task_comments_for_member", _fake_summary)
    response = client.post(f"/api/tasks/{task_id}/ai-comment-summary", headers=headers, json={})
    assert response.status_code == 200
    assert response.get_json()["meta"]["model"] == "test-model"

    class _FakeTaskOperationError(Exception):
        message = "AI 摘要服務暫時不可用，請稍後再試"
        status_code = 503

    def _raise_service_error(_task_id):
        raise _FakeTaskOperationError()

    monkeypatch.setattr("blueprints.tasks.TaskOperationError", _FakeTaskOperationError)
    monkeypatch.setattr("blueprints.tasks.summarize_task_comments_for_member", _raise_service_error)
    unavailable = client.post(f"/api/tasks/{task_id}/ai-comment-summary", headers=headers, json={})
    assert unavailable.status_code == 503


def test_ai_comment_summary_requires_member_and_handles_empty(client, auth_user_factory):
    auth_user_factory(
        email="task-summary-owner@example.com",
        password="Password123!",
        username="task_summary_owner_user",
    )
    auth_user_factory(
        email="task-summary-outsider@example.com",
        password="Password123!",
        username="task_summary_outsider_user",
    )
    owner_headers = _get_auth_headers(client, "task-summary-owner@example.com", "Password123!")
    outsider_headers = _get_auth_headers(client, "task-summary-outsider@example.com", "Password123!")
    task_id = _create_task(client, owner_headers, name="Summary empty")

    forbidden = client.post(f"/api/tasks/{task_id}/ai-comment-summary", headers=outsider_headers, json={})
    assert forbidden.status_code == 403

    response = client.post(f"/api/tasks/{task_id}/ai-comment-summary", headers=owner_headers, json={})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["meta"]["comment_count"] == 0
    assert payload["summary"]["decisions"] == []
    assert payload["summary"]["risks"] == []
    assert payload["summary"]["next_actions"] == []


def test_task_file_endpoints_handle_multipart_and_download(client, auth_user_factory):
    auth_user_factory(
        email="task-file-owner@example.com",
        password="Password123!",
        username="task_file_owner_user",
    )
    auth_user_factory(
        email="task-file-outsider@example.com",
        password="Password123!",
        username="task_file_outsider_user",
    )
    headers = _get_auth_headers(client, "task-file-owner@example.com", "Password123!")
    outsider_headers = _get_auth_headers(client, "task-file-outsider@example.com", "Password123!")
    task_id = _create_task(client, headers)

    no_file = client.post(
        f"/api/tasks/{task_id}/upload",
        headers=headers,
        data={},
        content_type="multipart/form-data",
    )
    assert no_file.status_code == 400

    unsupported = client.post(
        f"/api/tasks/{task_id}/upload",
        headers=headers,
        data={"file": (BytesIO(b"bad"), "file.exe")},
        content_type="multipart/form-data",
    )
    assert unsupported.status_code == 400

    upload = client.post(
        f"/api/tasks/{task_id}/upload",
        headers=headers,
        data={"file": (BytesIO(b"hello"), "report.txt")},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 201
    upload_payload = upload.get_json()

    list_response = client.get(f"/api/tasks/{task_id}/files", headers=headers)
    assert list_response.status_code == 200
    assert any(item["id"] == upload_payload["id"] for item in list_response.get_json())

    download_unauthorized = client.get(f"/api/tasks/files/{upload_payload['filename']}")
    assert download_unauthorized.status_code == 401

    download_forbidden = client.get(
        f"/api/tasks/files/{upload_payload['filename']}",
        headers=outsider_headers,
    )
    assert download_forbidden.status_code == 403

    download = client.get(
        f"/api/tasks/files/{upload_payload['filename']}",
        headers=headers,
    )
    assert download.status_code == 200
    assert download.data == b"hello"
    download.close()

    forbidden_delete = client.delete(
        f"/api/tasks/{task_id}/files/{upload_payload['id']}",
        headers=outsider_headers,
    )
    assert forbidden_delete.status_code == 403

    delete_response = client.delete(
        f"/api/tasks/{task_id}/files/{upload_payload['id']}",
        headers=headers,
    )
    assert delete_response.status_code == 200


def test_subtask_status_toggle_and_delete_endpoints(client, auth_user_factory):
    auth_user_factory(
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

    update_status = client.patch(
        f"/api/tasks/{task_id}/status",
        headers=headers,
        json={"status": "completed"},
    )
    assert update_status.status_code == 200
    assert update_status.get_json()["completed"] is True

    invalid_status = client.patch(
        f"/api/tasks/{task_id}/status",
        headers=headers,
        json={"status": "bad"},
    )
    assert invalid_status.status_code == 400

    toggle_task = client.patch(f"/api/tasks/{task_id}/toggle", headers=headers)
    assert toggle_task.status_code == 200

    delete_subtask = client.delete(
        f"/api/tasks/{task_id}/subtasks/{subtask_id}",
        headers=headers,
    )
    assert delete_subtask.status_code == 200


def test_delete_task_endpoint_maps_owner_guard_and_success(client, auth_user_factory):
    auth_user_factory(
        email="task-delete-owner@example.com",
        password="Password123!",
        username="task_delete_owner_user",
    )
    auth_user_factory(
        email="task-delete-outsider@example.com",
        password="Password123!",
        username="task_delete_outsider_user",
    )
    owner_headers = _get_auth_headers(client, "task-delete-owner@example.com", "Password123!")
    outsider_headers = _get_auth_headers(client, "task-delete-outsider@example.com", "Password123!")
    task_id = _create_task(client, owner_headers)

    forbidden = client.delete(f"/api/tasks/{task_id}", headers=outsider_headers)
    assert forbidden.status_code == 403

    success = client.delete(f"/api/tasks/{task_id}", headers=owner_headers)
    assert success.status_code == 200


def test_get_upcoming_tasks_includes_due_and_progress_items(client, auth_user_factory):
    user = auth_user_factory(
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
