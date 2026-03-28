from werkzeug.security import generate_password_hash

from models import db
from models.user import User


def _create_user(email: str, password: str, username: str) -> User:
    user = User(
        name="Blueprint Test User",
        username=username,
        email=email,
        password=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()
    return user


def _login(client, email: str, password: str) -> dict:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.get_json()


def test_register_success(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "New User",
            "username": "new_user",
            "email": "new-user@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert "user_id" in payload

    saved = User.query.filter_by(email="new-user@example.com").first()
    assert saved is not None


def test_register_missing_required_fields_returns_400(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "No Password User",
            "email": "missing-password@example.com",
        },
    )

    assert response.status_code == 400


def test_register_duplicate_email_returns_409(client):
    _create_user(
        email="dup-email@example.com",
        password="Password123!",
        username="dup_user",
    )

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Another User",
            "username": "another_dup",
            "email": "dup-email@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 409


def test_login_success_returns_tokens_and_user_payload(client):
    _create_user(
        email="login-success@example.com",
        password="Password123!",
        username="login_success_user",
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "login-success@example.com", "password": "Password123!"},
    )

    assert response.status_code == 200
    payload = response.get_json()

    assert "access_token" in payload
    assert "refresh_token" in payload
    assert payload["user"]["email"] == "login-success@example.com"


def test_login_wrong_password_returns_401(client):
    _create_user(
        email="wrong-password@example.com",
        password="Password123!",
        username="wrong_password_user",
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "wrong-password@example.com", "password": "WrongPassword!"},
    )

    assert response.status_code == 401


def test_me_requires_auth_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_with_access_token_returns_current_user(client):
    _create_user(
        email="me-endpoint@example.com",
        password="Password123!",
        username="me_endpoint_user",
    )

    login_payload = _login(client, "me-endpoint@example.com", "Password123!")
    headers = {"Authorization": f"Bearer {login_payload['access_token']}"}

    response = client.get("/api/auth/me", headers=headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["email"] == "me-endpoint@example.com"
    assert "phone" in payload


def test_refresh_with_refresh_token_returns_new_access_token(client):
    _create_user(
        email="refresh-endpoint@example.com",
        password="Password123!",
        username="refresh_endpoint_user",
    )

    login_payload = _login(client, "refresh-endpoint@example.com", "Password123!")
    headers = {"Authorization": f"Bearer {login_payload['refresh_token']}"}

    response = client.post("/api/auth/refresh", headers=headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert "access_token" in payload


def test_logout_with_access_token_returns_200(client):
    _create_user(
        email="logout-endpoint@example.com",
        password="Password123!",
        username="logout_endpoint_user",
    )

    login_payload = _login(client, "logout-endpoint@example.com", "Password123!")
    headers = {"Authorization": f"Bearer {login_payload['access_token']}"}

    response = client.post("/api/auth/logout", headers=headers)
    assert response.status_code == 200
