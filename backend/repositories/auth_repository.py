from models import db
from models.user import User


def get_user_by_email(email: str) -> User | None:
    return User.query.filter_by(email=email).first()


def get_user_by_username(username: str) -> User | None:
    return User.query.filter_by(username=username).first()


def get_user_by_id(user_id: int) -> User | None:
    return db.session.get(User, user_id)
