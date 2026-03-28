from werkzeug.security import generate_password_hash

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
