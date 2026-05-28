from datetime import datetime
from typing import Any
from sqlalchemy.orm import Query

from models import db
from models.message import Message, MessageRead
from repositories.message_repository import (
    build_unread_messages_query,
    count_unread_messages_for_user,
    get_user_by_id,
)
from repositories.session_repository import add_entity
from services.transactions import transaction


class MessageOperationError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def get_unread_messages_query(user_id: int) -> Query:
    return build_unread_messages_query(user_id)


def get_unread_message_count(user_id: int) -> int:
    return count_unread_messages_for_user(user_id)


def mark_all_unread_messages_as_read(user_id: int) -> None:
    unread_message_ids = [
        message_id
        for (message_id,) in get_unread_messages_query(user_id)
        .with_entities(Message.message_id)
        .all()
    ]

    if not unread_message_ids:
        return

    now = datetime.now()
    db.session.bulk_save_objects(
        [
            MessageRead(
                message_id=message_id,
                user_id=user_id,
                read_at=now,
            )
            for message_id in unread_message_ids
        ]
    )

    with transaction(MessageOperationError, '標記訊息失敗，請稍後再試'):
        pass


def serialize_group_message(message: Message, sender_name: str) -> dict[str, Any]:
    return {
        'message_id': message.message_id,
        'group_id': message.group_id,
        'sender_id': message.sender_id,
        'sender_name': sender_name,
        'content': message.content,
        'created_at': message.created_at.isoformat() + 'Z' if message.created_at else None,
    }


def create_group_message(group_id: int, sender_id: int, content: str) -> dict[str, Any]:
    sender = get_user_by_id(sender_id)
    if not sender:
        raise ValueError('使用者不存在')

    message = Message(group_id=group_id, sender_id=sender_id, content=content)
    with transaction(MessageOperationError, '建立訊息失敗，請稍後再試'):
        add_entity(message)
    return serialize_group_message(message, sender.name)
