from sqlalchemy import and_

from models import db
from models.message import Message, MessageRead
from models.user import User


def build_unread_messages_query(user_id):
    return db.session.query(Message).outerjoin(
        MessageRead,
        and_(
            Message.message_id == MessageRead.message_id,
            MessageRead.user_id == user_id,
        ),
    ).filter(MessageRead.message_id.is_(None))


def count_unread_messages_for_user(user_id):
    return build_unread_messages_query(user_id).count()


def get_user_by_id(user_id):
    return db.session.get(User, user_id)
