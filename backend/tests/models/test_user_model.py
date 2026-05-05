import pytest
from sqlalchemy.exc import IntegrityError

from models import db
from models.user import User
from tests.models.helpers import create_user


def test_user_requires_name(app):
    user = User(
        email="missing-name@example.com",
        password="hashed-password",
    )
    db.session.add(user)

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()


def test_user_email_must_be_unique(app):
    create_user("unique@example.com", username="u1")

    duplicated = User(
        name="Another User",
        username="u2",
        email="unique@example.com",
        password="hashed-password",
    )
    db.session.add(duplicated)

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()


def test_user_repr_contains_email(app):
    user = create_user("repr@example.com", username="repr_user")

    assert repr(user) == "<User repr@example.com>"
