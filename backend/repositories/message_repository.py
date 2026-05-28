from sqlalchemy import and_
from sqlalchemy.orm import Query

from models import db
from models.message import Message, MessageRead
from models.user import User


def build_unread_messages_query(user_id: int) -> Query:
    return db.session.query(Message).outerjoin(
        MessageRead,
        and_(
            Message.message_id == MessageRead.message_id,
            MessageRead.user_id == user_id,
        ),
    ).filter(MessageRead.message_id.is_(None))


def count_unread_messages_for_user(user_id: int) -> int:
    return build_unread_messages_query(user_id).count()


def get_user_by_id(user_id: int) -> User | None:
    return db.session.get(User, user_id)
