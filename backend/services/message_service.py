from models import db
from models.message import Message, MessageRead
from models.user import User


def get_unread_messages_query(user_id):
    return db.session.query(Message).outerjoin(
        MessageRead,
        db.and_(
            Message.message_id == MessageRead.message_id,
            MessageRead.user_id == user_id,
        ),
    ).filter(MessageRead.message_id.is_(None))


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
    sender = User.query.get(sender_id)
    if not sender:
        raise ValueError('使用者不存在')

    message = Message(group_id=group_id, sender_id=sender_id, content=content)
    db.session.add(message)
    db.session.commit()
    return serialize_group_message(message, sender.name)
