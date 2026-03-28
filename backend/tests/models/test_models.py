from sqlalchemy.exc import IntegrityError
import pytest

from models import db
from models.subtask import Subtask
from models.task import Task
from models.task_comment import TaskComment
from models.task_user import TaskUser
from models.timeline import TaskFile, Timeline
from models.timeline_user import TimelineUser
from models.user import User


def _create_user(email: str, username: str | None = None) -> User:
    user = User(
        name="Test User",
        username=username,
        email=email,
        password="hashed-password",
    )
    db.session.add(user)
    db.session.commit()
    return user


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
    _create_user("unique@example.com", username="u1")

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
    user = _create_user("repr@example.com", username="repr_user")

    assert repr(user) == "<User repr@example.com>"


def test_task_default_values(app):
    owner = _create_user("task-owner@example.com", username="task_owner")

    task = Task(user_id=owner.id, name="Default Task")
    db.session.add(task)
    db.session.commit()

    assert task.completed is False
    assert task.priority == 2
    assert task.status == "pending"
    assert task.created_at is not None
    assert repr(task) == "<Task Default Task>"


def test_task_user_unique_constraint(app):
    owner = _create_user("task-user-owner@example.com", username="task_user_owner")
    task = Task(user_id=owner.id, name="Task With Members")
    db.session.add(task)
    db.session.commit()

    first = TaskUser(task_id=task.task_id, user_id=owner.id, role=0)
    db.session.add(first)
    db.session.commit()

    duplicated = TaskUser(task_id=task.task_id, user_id=owner.id, role=1)
    db.session.add(duplicated)

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()


def test_timeline_user_unique_constraint(app):
    owner = _create_user("timeline-owner@example.com", username="timeline_owner")

    timeline = Timeline(user_id=owner.id, name="Timeline With Members")
    db.session.add(timeline)
    db.session.commit()

    first = TimelineUser(timeline_id=timeline.id, user_id=owner.id, role=0)
    db.session.add(first)
    db.session.commit()

    duplicated = TimelineUser(timeline_id=timeline.id, user_id=owner.id, role=1)
    db.session.add(duplicated)

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()


def test_delete_task_cascades_related_records(app):
    owner = _create_user("cascade-owner@example.com", username="cascade_owner")
    member = _create_user("cascade-member@example.com", username="cascade_member")

    timeline = Timeline(user_id=owner.id, name="Cascade Timeline")
    db.session.add(timeline)
    db.session.commit()

    task = Task(user_id=owner.id, name="Cascade Task", timeline_id=timeline.id)
    db.session.add(task)
    db.session.commit()

    db.session.add_all(
        [
            TaskUser(task_id=task.task_id, user_id=owner.id, role=0),
            TaskUser(task_id=task.task_id, user_id=member.id, role=1),
            TaskComment(task_id=task.task_id, user_id=owner.id, task_message="hello"),
            Subtask(task_id=task.task_id, name="subtask-1"),
            TaskFile(
                task_id=task.task_id,
                filename="file.bin",
                original_filename="file.bin",
                file_path="/tmp/file.bin",
                file_size=12,
                uploaded_by=owner.id,
            ),
        ]
    )
    db.session.commit()

    db.session.delete(task)
    db.session.commit()

    assert TaskUser.query.filter_by(task_id=task.task_id).count() == 0
    assert TaskComment.query.filter_by(task_id=task.task_id).count() == 0
    assert Subtask.query.filter_by(task_id=task.task_id).count() == 0
    assert TaskFile.query.filter_by(task_id=task.task_id).count() == 0


def test_delete_timeline_cascades_timeline_members(app):
    owner = _create_user("timeline-cascade-owner@example.com", username="timeline_c_owner")
    member = _create_user("timeline-cascade-member@example.com", username="timeline_c_member")

    timeline = Timeline(user_id=owner.id, name="Timeline Cascade")
    db.session.add(timeline)
    db.session.commit()

    db.session.add_all(
        [
            TimelineUser(timeline_id=timeline.id, user_id=owner.id, role=0),
            TimelineUser(timeline_id=timeline.id, user_id=member.id, role=1),
        ]
    )
    db.session.commit()

    db.session.delete(timeline)
    db.session.commit()

    assert TimelineUser.query.filter_by(timeline_id=timeline.id).count() == 0


def test_subtask_to_dict_has_iso_utc_suffix(app):
    owner = _create_user("subtask-owner@example.com", username="subtask_owner")
    task = Task(user_id=owner.id, name="Task For Subtask")
    db.session.add(task)
    db.session.commit()

    subtask = Subtask(task_id=task.task_id, name="child")
    db.session.add(subtask)
    db.session.commit()

    payload = subtask.to_dict()

    assert payload["id"] == subtask.id
    assert payload["task_id"] == task.task_id
    assert payload["name"] == "child"
    assert payload["created_at"].endswith("Z")
