from werkzeug.security import generate_password_hash
import blueprints.groups as groups_blueprint_module
import services.group_service as group_service_module

from models import db
from models.group import GroupMember
from models.user import User


def _create_user(email: str, password: str, username: str) -> User:
    user = User(
        name="Group Blueprint User",
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


def test_get_groups_requires_auth(client):
    response = client.get("/api/groups")
    assert response.status_code == 401


def test_create_group_success_and_creator_membership(client):
    owner = _create_user(
        email="group-create@example.com",
        password="Password123!",
        username="group_create_user",
    )
    headers = _get_auth_headers(client, "group-create@example.com", "Password123!")

    response = client.post(
        "/api/groups",
        headers=headers,
        json={"group_name": "Dev Team"},
    )

    assert response.status_code == 201
    payload = response.get_json()
    group_id = payload["group_id"]

    owner_member = GroupMember.query.filter_by(group_id=group_id, user_id=owner.id).first()
    assert owner_member is not None
    assert payload["invite_code"]


def test_join_group_success_for_second_user(client):
    _create_user(
        email="group-owner@example.com",
        password="Password123!",
        username="group_owner_user",
    )
    owner_headers = _get_auth_headers(client, "group-owner@example.com", "Password123!")

    create_response = client.post(
        "/api/groups",
        headers=owner_headers,
        json={"group_name": "Joinable Group"},
    )
    assert create_response.status_code == 201
    payload = create_response.get_json()
    group_id = payload["group_id"]
    invite_code = payload["invite_code"]

    member = _create_user(
        email="group-member@example.com",
        password="Password123!",
        username="group_member_user",
    )
    member_headers = _get_auth_headers(client, "group-member@example.com", "Password123!")

    join_response = client.post(
        "/api/groups/join",
        headers=member_headers,
        json={"invite_code": invite_code},
    )

    assert join_response.status_code == 200
    member_row = GroupMember.query.filter_by(group_id=group_id, user_id=member.id).first()
    assert member_row is not None


def test_send_and_fetch_group_message_for_member(client):
    _create_user(
        email="group-chat-owner@example.com",
        password="Password123!",
        username="group_chat_owner",
    )
    headers = _get_auth_headers(client, "group-chat-owner@example.com", "Password123!")

    create_response = client.post(
        "/api/groups",
        headers=headers,
        json={"group_name": "Chat Group"},
    )
    assert create_response.status_code == 201
    group_id = create_response.get_json()["group_id"]

    send_response = client.post(
        f"/api/groups/{group_id}/messages",
        headers=headers,
        json={"content": "hello group"},
    )
    assert send_response.status_code == 201

    list_response = client.get(f"/api/groups/{group_id}/messages", headers=headers)
    assert list_response.status_code == 200
    payload = list_response.get_json()
    assert any(item["content"] == "hello group" for item in payload)


def test_get_group_messages_blocks_non_member(client):
    _create_user(
        email="group-block-owner@example.com",
        password="Password123!",
        username="group_block_owner",
    )
    owner_headers = _get_auth_headers(client, "group-block-owner@example.com", "Password123!")

    create_response = client.post(
        "/api/groups",
        headers=owner_headers,
        json={"group_name": "Private Group"},
    )
    assert create_response.status_code == 201
    group_id = create_response.get_json()["group_id"]

    _create_user(
        email="group-outsider@example.com",
        password="Password123!",
        username="group_outsider",
    )
    outsider_headers = _get_auth_headers(client, "group-outsider@example.com", "Password123!")

    response = client.get(f"/api/groups/{group_id}/messages", headers=outsider_headers)
    assert response.status_code == 403


def test_leave_group_removes_membership(client):
    user = _create_user(
        email="group-leave@example.com",
        password="Password123!",
        username="group_leave_user",
    )
    headers = _get_auth_headers(client, "group-leave@example.com", "Password123!")

    create_response = client.post(
        "/api/groups",
        headers=headers,
        json={"group_name": "Leave Group"},
    )
    assert create_response.status_code == 201
    group_id = create_response.get_json()["group_id"]

    leave_response = client.post(f"/api/groups/{group_id}/leave", headers=headers)
    assert leave_response.status_code == 200

    member_row = GroupMember.query.filter_by(group_id=group_id, user_id=user.id).first()
    assert member_row is None


def test_create_group_requires_non_empty_name(client):
    _create_user(
        email="group-empty-name@example.com",
        password="Password123!",
        username="group_empty_name_user",
    )
    headers = _get_auth_headers(client, "group-empty-name@example.com", "Password123!")

    response = client.post(
        "/api/groups",
        headers=headers,
        json={"group_name": "   "},
    )

    assert response.status_code == 400


def test_join_group_invalid_and_duplicate(client):
    owner = _create_user(
        email="group-join-owner@example.com",
        password="Password123!",
        username="group_join_owner_user",
    )
    owner_headers = _get_auth_headers(client, "group-join-owner@example.com", "Password123!")

    create_response = client.post(
        "/api/groups",
        headers=owner_headers,
        json={"group_name": "Duplicate Join Group"},
    )
    assert create_response.status_code == 201
    invite_code = create_response.get_json()["invite_code"]

    invalid = client.post(
        "/api/groups/join",
        headers=owner_headers,
        json={"invite_code": "999999"},
    )
    assert invalid.status_code == 404

    duplicate = client.post(
        "/api/groups/join",
        headers=owner_headers,
        json={"invite_code": invite_code},
    )
    assert duplicate.status_code == 409
    assert owner.id is not None


def test_leave_group_returns_404_when_user_not_member(client):
    owner = _create_user(
        email="group-leave-owner404@example.com",
        password="Password123!",
        username="group_leave_owner404",
    )
    outsider = _create_user(
        email="group-leave-outsider404@example.com",
        password="Password123!",
        username="group_leave_outsider404",
    )
    owner_headers = _get_auth_headers(client, "group-leave-owner404@example.com", "Password123!")
    outsider_headers = _get_auth_headers(client, "group-leave-outsider404@example.com", "Password123!")

    create_response = client.post(
        "/api/groups",
        headers=owner_headers,
        json={"group_name": "Leave 404 Group"},
    )
    assert create_response.status_code == 201
    group_id = create_response.get_json()["group_id"]

    leave_response = client.post(f"/api/groups/{group_id}/leave", headers=outsider_headers)
    assert leave_response.status_code == 404
    assert owner.id != outsider.id


def test_send_group_message_validation_and_members_api(client):
    owner = _create_user(
        email="group-message-owner@example.com",
        password="Password123!",
        username="group_message_owner",
    )
    member = _create_user(
        email="group-message-member@example.com",
        password="Password123!",
        username="group_message_member",
    )
    outsider = _create_user(
        email="group-message-outsider@example.com",
        password="Password123!",
        username="group_message_outsider",
    )

    owner_headers = _get_auth_headers(client, "group-message-owner@example.com", "Password123!")
    member_headers = _get_auth_headers(client, "group-message-member@example.com", "Password123!")
    outsider_headers = _get_auth_headers(client, "group-message-outsider@example.com", "Password123!")

    create_response = client.post(
        "/api/groups",
        headers=owner_headers,
        json={"group_name": "Message Guard Group"},
    )
    assert create_response.status_code == 201
    payload = create_response.get_json()
    group_id = payload["group_id"]
    invite_code = payload["invite_code"]

    join_response = client.post(
        "/api/groups/join",
        headers=member_headers,
        json={"invite_code": invite_code},
    )
    assert join_response.status_code == 200

    members_response = client.get(f"/api/groups/{group_id}/members", headers=owner_headers)
    assert members_response.status_code == 200
    member_ids = {item["user_id"] for item in members_response.get_json()}
    assert owner.id in member_ids
    assert member.id in member_ids

    empty_message = client.post(
        f"/api/groups/{group_id}/messages",
        headers=owner_headers,
        json={"content": "   "},
    )
    assert empty_message.status_code == 400

    forbidden_message = client.post(
        f"/api/groups/{group_id}/messages",
        headers=outsider_headers,
        json={"content": "not allowed"},
    )
    assert forbidden_message.status_code == 403


def test_group_ai_snapshot_requires_member(client):
    _create_user(
        email="group-snapshot-owner@example.com",
        password="Password123!",
        username="group_snapshot_owner",
    )
    owner_headers = _get_auth_headers(client, "group-snapshot-owner@example.com", "Password123!")

    create_response = client.post(
        "/api/groups",
        headers=owner_headers,
        json={"group_name": "Snapshot Group"},
    )
    assert create_response.status_code == 201
    group_id = create_response.get_json()["group_id"]

    _create_user(
        email="group-snapshot-outsider@example.com",
        password="Password123!",
        username="group_snapshot_outsider",
    )
    outsider_headers = _get_auth_headers(client, "group-snapshot-outsider@example.com", "Password123!")

    response = client.post(
        f"/api/groups/{group_id}/ai-snapshot",
        headers=outsider_headers,
        json={"window_days": 30},
    )
    assert response.status_code == 403


def test_group_ai_snapshot_success_and_latest(client, monkeypatch):
    _create_user(
        email="group-snapshot-success@example.com",
        password="Password123!",
        username="group_snapshot_success",
    )
    headers = _get_auth_headers(client, "group-snapshot-success@example.com", "Password123!")

    create_response = client.post(
        "/api/groups",
        headers=headers,
        json={"group_name": "Snapshot Success Group"},
    )
    assert create_response.status_code == 201
    group_id = create_response.get_json()["group_id"]

    send_response_a = client.post(
        f"/api/groups/{group_id}/messages",
        headers=headers,
        json={"content": "今天決定先做 API"},
    )
    assert send_response_a.status_code == 201

    send_response_b = client.post(
        f"/api/groups/{group_id}/messages",
        headers=headers,
        json={"content": "明天補測試"},
    )
    assert send_response_b.status_code == 201

    class FakeSnapshotProvider:
        model = "fake-model"

        def generate_content(self, system_prompt, user_message, response_format="json"):
            return (
                '{"topics":[{"title":"API 實作","message_ids":[1]}],'
                '"decisions":[{"text":"先做後端 API","message_ids":[1]}],'
                '"action_items":[{"text":"補上測試","assignee":"Owner","message_ids":[2]}],'
                '"blockers":[{"text":"等待合併","message_ids":[2]}],'
                '"notable_quotes":[{"text":"明天補測試","message_id":2}]}'
            )

    monkeypatch.setattr(group_service_module, "get_ai_provider", lambda: FakeSnapshotProvider())

    snapshot_response = client.post(
        f"/api/groups/{group_id}/ai-snapshot",
        headers=headers,
        json={"window_days": 30, "async": False},
    )
    assert snapshot_response.status_code == 200
    payload = snapshot_response.get_json()
    assert payload["group_id"] == group_id
    assert payload["summary"]["topics"][0]["title"] == "API 實作"
    assert payload["summary"]["action_items"][0]["text"] == "補上測試"
    assert payload["summary"]["digest"]["todo_for_user"][0]["text"] == "補上測試"

    latest_response = client.get(
        f"/api/groups/{group_id}/ai-snapshot/latest",
        headers=headers,
    )
    assert latest_response.status_code == 200
    latest_payload = latest_response.get_json()
    assert latest_payload["snapshot_id"] == payload["snapshot_id"]


def test_group_ai_snapshot_async_job_status(client, monkeypatch):
    _create_user(
        email="group-snapshot-async@example.com",
        password="Password123!",
        username="group_snapshot_async",
    )
    headers = _get_auth_headers(client, "group-snapshot-async@example.com", "Password123!")

    create_response = client.post(
        "/api/groups",
        headers=headers,
        json={"group_name": "Snapshot Async Group"},
    )
    assert create_response.status_code == 201
    group_id = create_response.get_json()["group_id"]

    send_response = client.post(
        f"/api/groups/{group_id}/messages",
        headers=headers,
        json={"content": "大量訊息測試"},
    )
    assert send_response.status_code == 201

    monkeypatch.setattr(
        groups_blueprint_module,
        "enqueue_snapshot_job",
        lambda app, group_id, user_id, window_days: {
            "job_id": "job-demo-001",
            "status": "queued",
            "group_id": group_id,
            "requested_by": user_id,
            "window_days": window_days,
        },
    )
    monkeypatch.setattr(
        groups_blueprint_module,
        "get_snapshot_job_status",
        lambda job_id, requester_user_id=None: {
            "job_id": job_id,
            "status": "completed",
            "requested_by": requester_user_id,
            "snapshot_id": 123,
        },
    )

    snapshot_response = client.post(
        f"/api/groups/{group_id}/ai-snapshot",
        headers=headers,
        json={"window_days": 30, "async": True},
    )
    assert snapshot_response.status_code == 202
    assert snapshot_response.get_json()["job_id"] == "job-demo-001"

    status_response = client.get(
        "/api/groups/snapshot-jobs/job-demo-001",
        headers=headers,
    )
    assert status_response.status_code == 200
    status_payload = status_response.get_json()
    assert status_payload["status"] == "completed"
    assert status_payload["snapshot_id"] == 123
