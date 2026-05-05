import pytest
from sqlalchemy.exc import IntegrityError

from models import db
from models.subtask import Subtask
from models.task import Task
from models.task_comment import TaskComment
from models.task_user import TaskUser
from models.timeline import TaskFile, Timeline
from tests.models.helpers import create_user


def test_task_default_values(app):
    owner = create_user("task-owner@example.com", username="task_owner")

    task = Task(user_id=owner.id, name="Default Task")
    db.session.add(task)
    db.session.commit()

    assert task.completed is False
    assert task.completed_at is None
    assert task.depends_on_task_ids in (None, [])
    assert task.priority == 2
    assert task.status == "pending"
    assert task.created_at is not None
    assert repr(task) == "<Task Default Task>"


def test_task_user_unique_constraint(app):
    owner = create_user("task-user-owner@example.com", username="task_user_owner")
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


def test_delete_task_cascades_related_records(app):
    owner = create_user("cascade-owner@example.com", username="cascade_owner")
    member = create_user("cascade-member@example.com", username="cascade_member")

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


def test_subtask_to_dict_has_iso_utc_suffix(app):
    owner = create_user("subtask-owner@example.com", username="subtask_owner")
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
