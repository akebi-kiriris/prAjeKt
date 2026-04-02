from datetime import datetime

from models import db
from models.message import Message, MessageRead
from models.user import User


class MessageOperationError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def get_unread_messages_query(user_id):
    return db.session.query(Message).outerjoin(
        MessageRead,
        db.and_(
            Message.message_id == MessageRead.message_id,
            MessageRead.user_id == user_id,
        ),
    ).filter(MessageRead.message_id.is_(None))


def get_unread_message_count(user_id):
    return get_unread_messages_query(user_id).count()


def mark_all_unread_messages_as_read(user_id):
    unread_messages = get_unread_messages_query(user_id).all()

    for message in unread_messages:
        db.session.add(
            MessageRead(
                message_id=message.message_id,
                user_id=user_id,
                read_at=datetime.now(),
            )
        )

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise MessageOperationError('標記訊息失敗，請稍後再試', 500) from exc


def serialize_group_message(message, sender_name):
    return {
        'message_id': message.message_id,
        'group_id': message.group_id,
        'sender_id': message.sender_id,
        'sender_name': sender_name,
        'content': message.content,
        'created_at': message.created_at.isoformat() + 'Z' if message.created_at else None,
    }


def create_group_message(group_id, sender_id, content):
    sender = db.session.get(User, sender_id)
    if not sender:
        raise ValueError('使用者不存在')

    message = Message(group_id=group_id, sender_id=sender_id, content=content)
    db.session.add(message)
    db.session.commit()
    return serialize_group_message(message, sender.name)
