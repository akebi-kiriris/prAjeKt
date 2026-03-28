from models import db
from models.notification import Notification
from models.user import User
from werkzeug.security import generate_password_hash


def _create_user(email: str, password: str, username: str) -> User:
    user = User(
        name="Notification Blueprint User",
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


def _create_notification(user_id: int, title: str, is_read: bool = False) -> Notification:
    n = Notification(
        user_id=user_id,
        type="task_assigned",
        title=title,
        content="content",
        link="/tasks",
        is_read=is_read,
    )
    db.session.add(n)
    db.session.commit()
    return n


def test_get_notifications_requires_auth(client):
    response = client.get("/api/notifications")
    assert response.status_code == 401


def test_get_notifications_and_unread_count(client):
    user = _create_user(
        email="notif-list@example.com",
        password="Password123!",
        username="notif_list_user",
    )
    headers = _get_auth_headers(client, "notif-list@example.com", "Password123!")

    _create_notification(user.id, "n1", is_read=False)
    _create_notification(user.id, "n2", is_read=True)

    list_response = client.get("/api/notifications", headers=headers)
    assert list_response.status_code == 200
    payload = list_response.get_json()
    assert len(payload) == 2

    unread_response = client.get("/api/notifications/unread-count", headers=headers)
    assert unread_response.status_code == 200
    assert unread_response.get_json()["count"] == 1


def test_mark_as_read_and_mark_all_read(client):
    user = _create_user(
        email="notif-read@example.com",
        password="Password123!",
        username="notif_read_user",
    )
    headers = _get_auth_headers(client, "notif-read@example.com", "Password123!")

    first = _create_notification(user.id, "first", is_read=False)
    _create_notification(user.id, "second", is_read=False)

    mark_one_response = client.patch(f"/api/notifications/{first.id}/read", headers=headers)
    assert mark_one_response.status_code == 200

    mark_all_response = client.patch("/api/notifications/read-all", headers=headers)
    assert mark_all_response.status_code == 200

    unread_response = client.get("/api/notifications/unread-count", headers=headers)
    assert unread_response.status_code == 200
    assert unread_response.get_json()["count"] == 0


def test_delete_notification_success_and_not_found(client):
    user = _create_user(
        email="notif-delete@example.com",
        password="Password123!",
        username="notif_delete_user",
    )
    headers = _get_auth_headers(client, "notif-delete@example.com", "Password123!")

    notification = _create_notification(user.id, "to-delete", is_read=False)

    delete_response = client.delete(f"/api/notifications/{notification.id}", headers=headers)
    assert delete_response.status_code == 200
    assert Notification.query.filter_by(id=notification.id).first() is None

    missing_response = client.delete(f"/api/notifications/{notification.id}", headers=headers)
    assert missing_response.status_code == 404
