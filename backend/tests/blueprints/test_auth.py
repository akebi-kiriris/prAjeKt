
from models import db
from models.user import User



def _login(client, email: str, password: str) -> dict:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.get_json()


def test_register_success(client, auth_user_factory):
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


def test_register_missing_required_fields_returns_400(client, auth_user_factory):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "No Password User",
            "email": "missing-password@example.com",
        },
    )

    assert response.status_code == 400


def test_register_duplicate_email_returns_409(client, auth_user_factory):
    auth_user_factory(
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


def test_register_duplicate_username_returns_409(client, auth_user_factory):
    auth_user_factory(
        email="dup-username-a@example.com",
        password="Password123!",
        username="dup_username_user",
    )

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Another User",
            "username": "dup_username_user",
            "email": "dup-username-b@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 409


def test_register_username_optional_and_phone_supported(client, auth_user_factory):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "No Username User",
            "email": "no-username@example.com",
            "password": "Password123!",
            "phone": "0911222333",
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    saved = db.session.get(User, payload["user_id"])
    assert saved is not None
    assert saved.username is None
    assert saved.phone == "0911222333"


def test_register_normalizes_email_before_duplicate_check(client, auth_user_factory):
    auth_user_factory(
        email="normalize-email@example.com",
        password="Password123!",
        username="normalize_email_user",
    )

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Normalize Email",
            "username": "normalize_email_user_2",
            "email": "  NORMALIZE-EMAIL@EXAMPLE.COM  ",
            "password": "Password123!",
        },
    )

    assert response.status_code == 409


def test_login_success_returns_tokens_and_user_payload(client, auth_user_factory):
    auth_user_factory(
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


def test_login_wrong_password_returns_401(client, auth_user_factory):
    auth_user_factory(
        email="wrong-password@example.com",
        password="Password123!",
        username="wrong_password_user",
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "wrong-password@example.com", "password": "WrongPassword!"},
    )

    assert response.status_code == 401


def test_me_requires_auth_token(client, auth_user_factory):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_with_access_token_returns_current_user(client, auth_user_factory):
    auth_user_factory(
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


def test_refresh_with_refresh_token_returns_new_access_token(client, auth_user_factory):
    auth_user_factory(
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


def test_logout_with_access_token_returns_200(client, auth_user_factory):
    auth_user_factory(
        email="logout-endpoint@example.com",
        password="Password123!",
        username="logout_endpoint_user",
    )

    login_payload = _login(client, "logout-endpoint@example.com", "Password123!")
    headers = {"Authorization": f"Bearer {login_payload['access_token']}"}

    response = client.post("/api/auth/logout", headers=headers)
    assert response.status_code == 200
