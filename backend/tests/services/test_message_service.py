import pytest

from models import db
from models.message import Message, MessageRead
from models.user import User
from services.message_service import (
    create_group_message,
    get_unread_message_count,
    get_unread_messages_query,
    mark_all_unread_messages_as_read,
    serialize_group_message,
)



def test_message_service_create_and_serialize(app, user_factory):
    sender = user_factory("message-sender@example.com", "message_sender")

    payload = create_group_message(group_id=99, sender_id=sender.id, content="hello world")

    assert payload["sender_id"] == sender.id
    assert payload["content"] == "hello world"
    assert payload["sender_name"] == sender.name
    assert payload["created_at"].endswith("Z")


def test_message_service_create_group_message_user_missing(app, user_factory):
    with pytest.raises(ValueError):
        create_group_message(group_id=1, sender_id=99999, content="fail")


def test_message_service_get_unread_messages_query(app, user_factory):
    user = user_factory("message-unread@example.com", "message_unread_user")

    unread = Message(group_id=1, sender_id=user.id, content="unread")
    read = Message(group_id=1, sender_id=user.id, content="read")
    db.session.add_all([unread, read])
    db.session.commit()

    db.session.add(MessageRead(message_id=read.message_id, user_id=user.id))
    db.session.commit()

    results = get_unread_messages_query(user.id).all()
    unread_ids = {row.message_id for row in results}

    assert unread.message_id in unread_ids
    assert read.message_id not in unread_ids


def test_message_service_unread_count_and_mark_all_read(app, user_factory):
    user = user_factory("message-mark-all@example.com", "message_mark_all_user")
    sender = user_factory("message-mark-all-sender@example.com", "message_mark_all_sender")

    read_message = Message(group_id=1, sender_id=sender.id, content="read")
    unread_message_a = Message(group_id=1, sender_id=sender.id, content="unread a")
    unread_message_b = Message(group_id=1, sender_id=sender.id, content="unread b")
    db.session.add_all([read_message, unread_message_a, unread_message_b])
    db.session.flush()

    db.session.add(MessageRead(message_id=read_message.message_id, user_id=user.id))
    db.session.commit()

    assert get_unread_message_count(user.id) == 2

    mark_all_unread_messages_as_read(user.id)

    assert get_unread_message_count(user.id) == 0
    assert MessageRead.query.filter_by(user_id=user.id).count() == 3


def test_message_service_serialize_group_message(app, user_factory):
    user = user_factory("message-serialize@example.com", "message_serialize_user")
    message = Message(group_id=2, sender_id=user.id, content="serialize")
    db.session.add(message)
    db.session.commit()

    payload = serialize_group_message(message, "Sender")

    assert payload["message_id"] == message.message_id
    assert payload["sender_name"] == "Sender"
    assert payload["created_at"].endswith("Z")
