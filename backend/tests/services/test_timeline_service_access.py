from datetime import date, datetime

from models import db
from models.task import Task
from models.task_user import TaskUser
from models.timeline import Timeline
from models.timeline_user import TimelineUser
from models.user import User
from services.timeline_service import (
    get_task_access,
    get_user_timeline_role,
    timeline_list_item_to_dict,
    timeline_member_item_to_dict,
    timeline_task_item_to_dict,
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


def test_timeline_role_and_task_access_resolution(app):
    owner = _create_user("timeline-access-owner@example.com", "timeline_access_owner")
    member = _create_user("timeline-access-member@example.com", "timeline_access_member")
    outsider = _create_user("timeline-access-outsider@example.com", "timeline_access_outsider")

    timeline = Timeline(user_id=owner.id, name="Access Timeline")
    db.session.add(timeline)
    db.session.commit()

    timeline_task = Task(user_id=owner.id, name="Timeline Task", timeline_id=timeline.id)
    solo_task = Task(user_id=owner.id, name="Solo Task")
    db.session.add_all([timeline_task, solo_task])
    db.session.commit()

    db.session.add(TimelineUser(timeline_id=timeline.id, user_id=member.id, role=1))
    db.session.add(TaskUser(task_id=solo_task.task_id, user_id=member.id, role=1))
    db.session.commit()

    assert get_user_timeline_role(member.id, timeline.id) == 1
    assert get_user_timeline_role(outsider.id, timeline.id) is None

    assert get_task_access(member.id, timeline_task) == 1
    assert get_task_access(member.id, solo_task) == 1
    assert get_task_access(owner.id, solo_task) == 0
    assert get_task_access(outsider.id, solo_task) is None


def test_timeline_serializers(app):
    owner = _create_user("timeline-serializer-owner@example.com", "timeline_serializer_owner")

    timeline = Timeline(
        user_id=owner.id,
        name="Serializer Timeline",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 10),
        remark="remark",
    )
    db.session.add(timeline)
    db.session.commit()

    timeline_payload = timeline_list_item_to_dict(
        timeline,
        role=0,
        total_tasks=3,
        completed_tasks=1,
    )

    task = Task(
        user_id=owner.id,
        name="Timeline Serializer Task",
        timeline_id=timeline.id,
        start_date=datetime(2026, 1, 2, 9, 0, 0),
        end_date=datetime(2026, 1, 3, 9, 0, 0),
    )
    db.session.add(task)
    db.session.commit()

    task_payload = timeline_task_item_to_dict(task, assignee_name="Owner", assistant_list=["A"])

    member = TimelineUser(timeline_id=timeline.id, user_id=owner.id, role=0)
    db.session.add(member)
    db.session.commit()

    member_payload = timeline_member_item_to_dict(member, owner)

    assert timeline_payload["id"] == timeline.id
    assert timeline_payload["startDate"].endswith("Z")
    assert task_payload["assignee"] == "Owner"
    assert task_payload["depends_on_task_ids"] == []
    assert task_payload["can_manage_members"] is False
    assert task_payload["start_date"].endswith("Z")
    assert member_payload["email"] == owner.email
