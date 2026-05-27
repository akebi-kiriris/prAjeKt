
from models import db
from models.user import User



def _get_auth_headers(client, email: str, password: str) -> dict:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_profile_requires_auth(client, auth_user_factory):
    response = client.get("/api/profile/me")
    assert response.status_code == 401


def test_get_profile_returns_current_user(client, auth_user_factory):
    auth_user_factory(
        email="profile-me@example.com",
        password="Password123!",
        username="profile_me_user",
    )
    headers = _get_auth_headers(client, "profile-me@example.com", "Password123!")

    response = client.get("/api/profile/me", headers=headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["email"] == "profile-me@example.com"
    assert "created_at" in payload


def test_update_profile_rejects_unknown_fields(client, auth_user_factory):
    auth_user_factory(
        email="profile-unknown@example.com",
        password="Password123!",
        username="profile_unknown_user",
    )
    headers = _get_auth_headers(client, "profile-unknown@example.com", "Password123!")

    response = client.put(
        "/api/profile/me",
        headers=headers,
        json={"bad_field": "x"},
    )

    assert response.status_code == 400


def test_update_profile_rejects_duplicate_username(client, auth_user_factory):
    auth_user_factory(
        email="profile-owner@example.com",
        password="Password123!",
        username="profile_owner_user",
    )
    auth_user_factory(
        email="profile-another@example.com",
        password="Password123!",
        username="already_taken_username",
    )
    headers = _get_auth_headers(client, "profile-owner@example.com", "Password123!")

    response = client.put(
        "/api/profile/me",
        headers=headers,
        json={"username": "already_taken_username"},
    )

    assert response.status_code == 409


def test_update_profile_rejects_duplicate_email(client, auth_user_factory):
    auth_user_factory(
        email="profile-email-owner@example.com",
        password="Password123!",
        username="profile_email_owner_user",
    )
    auth_user_factory(
        email="profile-email-taken@example.com",
        password="Password123!",
        username="profile_email_taken_user",
    )
    headers = _get_auth_headers(client, "profile-email-owner@example.com", "Password123!")

    response = client.put(
        "/api/profile/me",
        headers=headers,
        json={"email": "profile-email-taken@example.com"},
    )

    assert response.status_code == 409


def test_update_profile_password_requires_current_password(client, auth_user_factory):
    auth_user_factory(
        email="profile-password@example.com",
        password="Password123!",
        username="profile_password_user",
    )
    headers = _get_auth_headers(client, "profile-password@example.com", "Password123!")

    response = client.put(
        "/api/profile/me",
        headers=headers,
        json={"new_password": "NewPassword123!"},
    )

    assert response.status_code == 400


def test_search_user_success_and_not_found(client, auth_user_factory):
    auth_user_factory(
        email="profile-search-owner@example.com",
        password="Password123!",
        username="profile_search_owner",
    )
    auth_user_factory(
        email="profile-search-target@example.com",
        password="Password123!",
        username="profile_search_target",
    )
    headers = _get_auth_headers(client, "profile-search-owner@example.com", "Password123!")

    ok_response = client.post(
        "/api/profile/search",
        headers=headers,
        json={"query": "profile_search_target"},
    )
    assert ok_response.status_code == 200
    assert ok_response.get_json()["email"] == "profile-search-target@example.com"

    miss_response = client.post(
        "/api/profile/search",
        headers=headers,
        json={"query": "not_found_user_123"},
    )
    assert miss_response.status_code == 404


def test_chart_stats_returns_expected_shape(client, auth_user_factory):
    auth_user_factory(
        email="profile-stats@example.com",
        password="Password123!",
        username="profile_stats_user",
    )
    headers = _get_auth_headers(client, "profile-stats@example.com", "Password123!")

    response = client.get("/api/profile/chart-stats", headers=headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert "status_distribution" in payload
    assert "daily_completions" in payload
    assert "tasks_by_project" in payload
    assert len(payload["daily_completions"]) == 30
