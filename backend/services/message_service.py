from app import db
from models.message import Message, MessageRead


def get_unread_messages_query(user_id):
    return db.session.query(Message).outerjoin(
        MessageRead,
        db.and_(
            Message.message_id == MessageRead.message_id,
            MessageRead.user_id == user_id,
        ),
    ).filter(MessageRead.message_id.is_(None))
