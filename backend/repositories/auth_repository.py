from models import db
from models.user import User


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def get_user_by_username(username):
    return User.query.filter_by(username=username).first()


def get_user_by_id(user_id):
    return db.session.get(User, user_id)
