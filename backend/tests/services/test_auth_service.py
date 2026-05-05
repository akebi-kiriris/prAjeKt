import pytest

from models import db
from models.user import User
from services.auth_service import (
    AuthOperationError,
    auth_user_to_dict,
    authenticate_user,
    current_user_to_dict,
    get_current_user_or_404,
    register_user,
)


def _create_user(email: str, username: str) -> User:
    user = User(
        name="Service Test User",
        username=username,
        email=email,
        password="hashed-password",
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_auth_service_serializers(app):
    user = _create_user("auth-service@example.com", "auth_service_user")
    user.phone = "0912345678"
    db.session.commit()

    auth_payload = auth_user_to_dict(user)
    current_payload = current_user_to_dict(user)

    assert auth_payload == {
        "id": user.id,
        "name": user.name,
        "username": user.username,
        "email": user.email,
    }
    assert current_payload["phone"] == "0912345678"


def test_auth_service_operations_and_errors(app):
    user_id = register_user(
        {
            "name": "Auth Ops",
            "username": "auth_ops_user",
            "email": "auth-ops@example.com",
            "password": "Password123!",
            "phone": "0912000111",
        }
    )

    user = db.session.get(User, user_id)
    assert user is not None
    assert user.email == "auth-ops@example.com"

    authenticated = authenticate_user("auth-ops@example.com", "Password123!")
    assert authenticated.id == user_id

    loaded = get_current_user_or_404(user_id)
    assert loaded.id == user_id

    with pytest.raises(AuthOperationError) as duplicate_exc:
        register_user(
            {
                "name": "Another",
                "username": "auth_ops_user_2",
                "email": "auth-ops@example.com",
                "password": "Password123!",
            }
        )
    assert duplicate_exc.value.status_code == 409

    with pytest.raises(AuthOperationError) as missing_exc:
        register_user({"name": "Missing Password", "email": "missing-auth@example.com"})
    assert missing_exc.value.status_code == 400

    with pytest.raises(AuthOperationError) as wrong_password_exc:
        authenticate_user("auth-ops@example.com", "WrongPassword")
    assert wrong_password_exc.value.status_code == 401

    with pytest.raises(AuthOperationError) as not_found_exc:
        get_current_user_or_404(999999)
    assert not_found_exc.value.status_code == 404
