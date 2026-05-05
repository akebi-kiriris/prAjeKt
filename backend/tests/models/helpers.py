from models import db
from models.user import User


def create_user(email: str, username: str | None = None) -> User:
    user = User(
        name="Test User",
        username=username,
        email=email,
        password="hashed-password",
    )
    db.session.add(user)
    db.session.commit()
    return user
