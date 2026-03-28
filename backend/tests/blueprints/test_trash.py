from datetime import datetime, timezone

from models import db
from models.task import Task
from models.timeline import Timeline
from models.user import User
from werkzeug.security import generate_password_hash


def _now_naive_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _create_user(email: str, password: str, username: str) -> User:
    user = User(
        name="Trash Blueprint User",
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


def test_get_trash_requires_auth(client):
    response = client.get("/api/trash")
    assert response.status_code == 401


def test_get_trash_returns_soft_deleted_owned_items(client):
    user = _create_user(
        email="trash-list@example.com",
        password="Password123!",
        username="trash_list_user",
    )
    headers = _get_auth_headers(client, "trash-list@example.com", "Password123!")

    timeline = Timeline(user_id=user.id, name="Trash Timeline", deleted_at=_now_naive_utc())
    db.session.add(timeline)
    db.session.commit()

    task = Task(user_id=user.id, name="Trash Task", deleted_at=_now_naive_utc(), timeline_id=timeline.id)
    db.session.add(task)
    db.session.commit()

    response = client.get("/api/trash", headers=headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert any(item["task_id"] == task.task_id for item in payload["tasks"])
    assert any(item["id"] == timeline.id for item in payload["timelines"])


def test_restore_task_and_restore_timeline(client):
    user = _create_user(
        email="trash-restore@example.com",
        password="Password123!",
        username="trash_restore_user",
    )
    headers = _get_auth_headers(client, "trash-restore@example.com", "Password123!")

    task = Task(user_id=user.id, name="Restore Task", deleted_at=_now_naive_utc())
    timeline = Timeline(user_id=user.id, name="Restore Timeline", deleted_at=_now_naive_utc())
    db.session.add_all([task, timeline])
    db.session.commit()

    restore_task_response = client.patch(f"/api/trash/tasks/{task.task_id}/restore", headers=headers)
    assert restore_task_response.status_code == 200

    restore_timeline_response = client.patch(f"/api/trash/timelines/{timeline.id}/restore", headers=headers)
    assert restore_timeline_response.status_code == 200

    assert db.session.get(Task, task.task_id).deleted_at is None
    assert db.session.get(Timeline, timeline.id).deleted_at is None


def test_permanently_delete_task(client):
    user = _create_user(
        email="trash-delete-task@example.com",
        password="Password123!",
        username="trash_delete_task_user",
    )
    headers = _get_auth_headers(client, "trash-delete-task@example.com", "Password123!")

    task = Task(user_id=user.id, name="Delete Task", deleted_at=_now_naive_utc())
    db.session.add(task)
    db.session.commit()

    response = client.delete(f"/api/trash/tasks/{task.task_id}", headers=headers)

    assert response.status_code == 200
    assert db.session.get(Task, task.task_id) is None


def test_permanently_delete_timeline_cascades_tasks(client):
    user = _create_user(
        email="trash-delete-timeline@example.com",
        password="Password123!",
        username="trash_delete_timeline_user",
    )
    headers = _get_auth_headers(client, "trash-delete-timeline@example.com", "Password123!")

    timeline = Timeline(user_id=user.id, name="Delete Timeline", deleted_at=_now_naive_utc())
    db.session.add(timeline)
    db.session.commit()

    task = Task(user_id=user.id, timeline_id=timeline.id, name="Child Task", deleted_at=_now_naive_utc())
    db.session.add(task)
    db.session.commit()

    response = client.delete(f"/api/trash/timelines/{timeline.id}", headers=headers)

    assert response.status_code == 200
    assert db.session.get(Task, task.task_id) is None
    assert db.session.get(Timeline, timeline.id) is None


def test_restore_task_denies_non_owner(client):
    owner = _create_user(
        email="trash-owner@example.com",
        password="Password123!",
        username="trash_owner_user",
    )
    outsider = _create_user(
        email="trash-outsider@example.com",
        password="Password123!",
        username="trash_outsider_user",
    )

    outsider_headers = _get_auth_headers(client, "trash-outsider@example.com", "Password123!")

    task = Task(user_id=owner.id, name="Owner Task", deleted_at=_now_naive_utc())
    db.session.add(task)
    db.session.commit()

    response = client.patch(f"/api/trash/tasks/{task.task_id}/restore", headers=outsider_headers)

    assert response.status_code == 404
