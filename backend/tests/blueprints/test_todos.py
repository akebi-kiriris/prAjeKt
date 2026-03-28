from werkzeug.security import generate_password_hash

from models import db
from models.user import User


def _create_user(email: str, password: str, username: str) -> User:
    user = User(
        name="Todo Blueprint User",
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


def test_get_todos_requires_auth(client):
    response = client.get("/api/todos")
    assert response.status_code == 401


def test_create_todo_and_get_todo_list(client):
    _create_user(
        email="todo-list@example.com",
        password="Password123!",
        username="todo_list_user",
    )
    headers = _get_auth_headers(client, "todo-list@example.com", "Password123!")

    create_response = client.post(
        "/api/todos",
        headers=headers,
        json={
            "title": "Buy milk",
            "content": "Buy 2 liters",
            "priority": 1,
        },
    )

    assert create_response.status_code == 201
    todo_id = create_response.get_json()["id"]

    list_response = client.get("/api/todos", headers=headers)
    assert list_response.status_code == 200

    payload = list_response.get_json()
    assert isinstance(payload, list)
    assert any(item["id"] == todo_id for item in payload)


def test_create_todo_rejects_unknown_fields(client):
    _create_user(
        email="todo-unknown-field@example.com",
        password="Password123!",
        username="todo_unknown_field_user",
    )
    headers = _get_auth_headers(client, "todo-unknown-field@example.com", "Password123!")

    response = client.post(
        "/api/todos",
        headers=headers,
        json={
            "title": "Task title",
            "content": "Task content",
            "not_allowed": "value",
        },
    )

    assert response.status_code == 400


def test_toggle_todo_switches_completed_state(client):
    _create_user(
        email="todo-toggle@example.com",
        password="Password123!",
        username="todo_toggle_user",
    )
    headers = _get_auth_headers(client, "todo-toggle@example.com", "Password123!")

    create_response = client.post(
        "/api/todos",
        headers=headers,
        json={
            "title": "Toggle me",
            "content": "Toggle content",
        },
    )
    assert create_response.status_code == 201
    todo_id = create_response.get_json()["id"]

    first_toggle = client.patch(f"/api/todos/{todo_id}/toggle", headers=headers)
    assert first_toggle.status_code == 200
    assert first_toggle.get_json()["completed"] is True

    second_toggle = client.patch(f"/api/todos/{todo_id}/toggle", headers=headers)
    assert second_toggle.status_code == 200
    assert second_toggle.get_json()["completed"] is False


def test_update_todo_rejects_invalid_priority(client):
    _create_user(
        email="todo-update-priority@example.com",
        password="Password123!",
        username="todo_update_priority_user",
    )
    headers = _get_auth_headers(client, "todo-update-priority@example.com", "Password123!")

    create_response = client.post(
        "/api/todos",
        headers=headers,
        json={
            "title": "Update me",
            "content": "Content",
        },
    )
    assert create_response.status_code == 201
    todo_id = create_response.get_json()["id"]

    response = client.put(
        f"/api/todos/{todo_id}",
        headers=headers,
        json={"priority": 9},
    )

    assert response.status_code == 400
