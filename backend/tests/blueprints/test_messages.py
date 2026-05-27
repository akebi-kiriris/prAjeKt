
from models import db
from models.message import Message, MessageRead
from models.user import User



def _get_auth_headers(client, email: str, password: str) -> dict:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_unread_count_requires_auth(client, auth_user_factory):
    response = client.get("/api/messages/unread-count")
    assert response.status_code == 401


def test_get_unread_count_returns_only_unread_messages(client, auth_user_factory):
    user = auth_user_factory(
        email="message-count-user@example.com",
        password="Password123!",
        username="message_count_user",
    )
    sender = auth_user_factory(
        email="message-count-sender@example.com",
        password="Password123!",
        username="message_count_sender",
    )
    headers = _get_auth_headers(client, "message-count-user@example.com", "Password123!")

    read_message = Message(sender_id=sender.id, content="already read")
    unread_message_a = Message(sender_id=sender.id, content="unread A")
    unread_message_b = Message(sender_id=sender.id, content="unread B")
    db.session.add_all([read_message, unread_message_a, unread_message_b])
    db.session.flush()

    db.session.add(MessageRead(message_id=read_message.message_id, user_id=user.id))
    db.session.commit()

    response = client.get("/api/messages/unread-count", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["unread_count"] == 2


def test_mark_all_as_read_marks_every_unread_message(client, auth_user_factory):
    user = auth_user_factory(
        email="message-mark-user@example.com",
        password="Password123!",
        username="message_mark_user",
    )
    sender = auth_user_factory(
        email="message-mark-sender@example.com",
        password="Password123!",
        username="message_mark_sender",
    )
    headers = _get_auth_headers(client, "message-mark-user@example.com", "Password123!")

    message_a = Message(sender_id=sender.id, content="mark A")
    message_b = Message(sender_id=sender.id, content="mark B")
    db.session.add_all([message_a, message_b])
    db.session.commit()

    mark_response = client.post("/api/messages/mark-all-read", headers=headers)
    assert mark_response.status_code == 200

    read_records = MessageRead.query.filter_by(user_id=user.id).all()
    assert len(read_records) == 2

    unread_response = client.get("/api/messages/unread-count", headers=headers)
    assert unread_response.status_code == 200
    assert unread_response.get_json()["unread_count"] == 0
