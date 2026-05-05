from datetime import datetime

from models import db
from models.task import Task
from models.task_comment import TaskComment
from models.task_user import TaskUser
from models.user import User
from services.task_service import (
    build_task_member_list,
    task_comment_to_dict,
    task_list_item_to_dict,
    task_member_to_dict,
)


def _create_user(email: str, username: str) -> User:
    user = User(
        name="Task Service User",
        username=username,
        email=email,
        password="hashed-password",
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_task_member_serializers(app):
    owner = _create_user("task-member-owner@example.com", "task_member_owner")
    task = Task(user_id=owner.id, name="Member Task")
    db.session.add(task)
    db.session.commit()

    member = TaskUser(task_id=task.task_id, user_id=owner.id, role=0)
    db.session.add(member)
    db.session.commit()

    payload_without_contact = task_member_to_dict(member, owner, include_contact=False)
    payload_with_contact = task_member_to_dict(member, owner, include_contact=True)

    assert "email" not in payload_without_contact
    assert payload_with_contact["email"] == owner.email
    assert payload_with_contact["assigned_at"].endswith("Z")


def test_build_task_member_list_returns_viewer_role(app):
    owner = _create_user("member-list-owner@example.com", "member_list_owner")
    member = _create_user("member-list-member@example.com", "member_list_member")

    task = Task(user_id=owner.id, name="Member List Task")
    db.session.add(task)
    db.session.commit()

    db.session.add(TaskUser(task_id=task.task_id, user_id=owner.id, role=0))
    db.session.add(TaskUser(task_id=task.task_id, user_id=member.id, role=1))
    db.session.commit()

    payload, viewer_role = build_task_member_list(
        task.task_id,
        viewer_user_id=member.id,
        include_contact=True,
    )

    assert len(payload) == 2
    assert viewer_role == 1
    assert all("email" in row for row in payload)


def test_task_list_item_and_comment_serializers(app):
    owner = _create_user("task-serializer-owner@example.com", "task_serializer_owner")
    task = Task(
        user_id=owner.id,
        name="Serializer Task",
        priority=1,
        status="in_progress",
        tags="a,b",
        task_remark="remark",
        isWork=1,
        start_date=datetime(2026, 1, 1, 10, 0, 0),
        end_date=datetime(2026, 1, 2, 10, 0, 0),
    )
    db.session.add(task)
    db.session.commit()

    list_payload = task_list_item_to_dict(
        task,
        member_list=[{"user_id": owner.id}],
        subtask_list=[{"id": 1}],
        is_owner=True,
    )

    comment = TaskComment(task_id=task.task_id, user_id=owner.id, task_message="hello")
    db.session.add(comment)
    db.session.commit()

    comment_payload = task_comment_to_dict(comment, user=None)

    assert list_payload["task_id"] == task.task_id
    assert list_payload["created_at"].endswith("Z")
    assert list_payload["is_owner"] is True
    assert comment_payload["user_name"] == "未知使用者"
