import pytest

from models import db
from models.task import Task
from models.timeline import Timeline
from models.timeline_user import TimelineUser
from models.user import User
from services.profile_service import (
    ProfileOperationError,
    build_chart_stats_for_user,
    find_unknown_fields as profile_find_unknown_fields,
    get_profile_user_or_404,
    profile_to_dict,
    search_user_by_query,
    search_user_to_dict,
    update_profile_for_user,
)



def test_profile_service_helpers_and_serializers(app, user_factory):
    unknown = profile_find_unknown_fields(
        {"name": "A", "x": 1, "z": 2},
        {"name", "email"},
    )
    assert unknown == ["x", "z"]

    user = user_factory("profile-service@example.com", "profile_service_user")
    user.bio = "about"
    user.avatar = "https://example.com/avatar.png"
    db.session.commit()

    profile_payload = profile_to_dict(user)
    search_payload = search_user_to_dict(user)

    assert profile_payload["created_at"].endswith("Z")
    assert profile_payload["bio"] == "about"
    assert search_payload == {
        "id": user.id,
        "name": user.name,
        "username": user.username,
        "email": user.email,
    }


def test_profile_service_update_search_and_chart_stats(app, user_factory):
    user = user_factory("profile-service-ops@example.com", "profile_service_ops")
    target = user_factory("profile-service-target@example.com", "profile_service_target")

    loaded = get_profile_user_or_404(user.id)
    assert loaded.id == user.id

    update_profile_for_user(
        user.id,
        {
            "name": "Updated Name",
            "phone": "0911222333",
            "bio": "updated bio",
        },
    )
    refreshed = db.session.get(User, user.id)
    assert refreshed.name == "Updated Name"
    assert refreshed.phone == "0911222333"

    found = search_user_by_query(target.username)
    assert found.id == target.id

    timeline = Timeline(user_id=user.id, name="Profile Stats Timeline")
    db.session.add(timeline)
    db.session.flush()
    db.session.add(TimelineUser(timeline_id=timeline.id, user_id=user.id, role=0))

    completed_task = Task(
        user_id=user.id,
        timeline_id=timeline.id,
        name="completed",
        completed=True,
        status="completed",
    )
    active_task = Task(
        user_id=user.id,
        timeline_id=timeline.id,
        name="active",
        completed=False,
        status="in_progress",
    )
    db.session.add_all([completed_task, active_task])
    db.session.commit()

    stats = build_chart_stats_for_user(user.id)
    assert "status_distribution" in stats
    assert "daily_completions" in stats
    assert "tasks_by_project" in stats
    assert len(stats["daily_completions"]) == 30


def test_profile_service_validation_errors(app, user_factory):
    owner = user_factory("profile-service-owner@example.com", "profile_service_owner")
    duplicate = user_factory("profile-service-dup@example.com", "profile_service_dup")

    with pytest.raises(ProfileOperationError) as unknown_exc:
        update_profile_for_user(owner.id, {"bad_field": "x"})
    assert unknown_exc.value.status_code == 400

    with pytest.raises(ProfileOperationError) as username_exc:
        update_profile_for_user(owner.id, {"username": duplicate.username})
    assert username_exc.value.status_code == 409

    with pytest.raises(ProfileOperationError) as email_exc:
        update_profile_for_user(owner.id, {"email": duplicate.email})
    assert email_exc.value.status_code == 409

    with pytest.raises(ProfileOperationError) as search_exc:
        search_user_by_query(" ")
    assert search_exc.value.status_code == 400
