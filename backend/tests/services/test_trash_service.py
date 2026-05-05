from datetime import datetime, timezone

import pytest

from models import db
from models.task import Task
from models.task_user import TaskUser
from models.timeline import Timeline
from models.timeline_user import TimelineUser
from models.user import User
from services.trash_service import (
    TrashOperationError,
    get_trash_payload,
    permanently_delete_task_for_owner,
    permanently_delete_timeline_for_owner,
    restore_task_for_owner,
    restore_timeline_for_owner,
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


def test_trash_service_get_payload_includes_owned_and_member_deleted(app):
    owner = _create_user("trash-service-owner@example.com", "trash_service_owner")
    member = _create_user("trash-service-member@example.com", "trash_service_member")

    owned_task = Task(user_id=member.id, name="owned deleted", deleted_at=datetime.now(timezone.utc).replace(tzinfo=None))
    db.session.add(owned_task)
    db.session.flush()

    foreign_task = Task(user_id=owner.id, name="member deleted", deleted_at=datetime.now(timezone.utc).replace(tzinfo=None))
    db.session.add(foreign_task)
    db.session.flush()
    db.session.add(TaskUser(task_id=foreign_task.task_id, user_id=member.id, role=1))

    owned_timeline = Timeline(
        user_id=member.id,
        name="owned deleted timeline",
        deleted_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.session.add(owned_timeline)
    db.session.flush()

    foreign_timeline = Timeline(
        user_id=owner.id,
        name="member deleted timeline",
        deleted_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.session.add(foreign_timeline)
    db.session.flush()
    db.session.add(TimelineUser(timeline_id=foreign_timeline.id, user_id=member.id, role=1))
    db.session.commit()

    payload = get_trash_payload(member.id)

    task_ids = {item["task_id"] for item in payload["tasks"]}
    timeline_ids = {item["id"] for item in payload["timelines"]}

    assert owned_task.task_id in task_ids
    assert foreign_task.task_id in task_ids
    assert owned_timeline.id in timeline_ids
    assert foreign_timeline.id in timeline_ids


def test_trash_service_restore_and_delete_operations(app):
    owner = _create_user("trash-service-op-owner@example.com", "trash_service_op_owner")

    task = Task(
        user_id=owner.id,
        name="restore then delete task",
        deleted_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    timeline = Timeline(
        user_id=owner.id,
        name="restore then delete timeline",
        deleted_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.session.add_all([task, timeline])
    db.session.commit()

    restore_task_for_owner(task.task_id, owner.id)
    restore_timeline_for_owner(timeline.id, owner.id)

    assert db.session.get(Task, task.task_id).deleted_at is None
    assert db.session.get(Timeline, timeline.id).deleted_at is None

    db.session.get(Task, task.task_id).deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.get(Timeline, timeline.id).deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    child_task = Task(
        user_id=owner.id,
        timeline_id=timeline.id,
        name="child deleted",
        deleted_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.session.add(child_task)
    db.session.commit()

    permanently_delete_task_for_owner(task.task_id, owner.id)
    permanently_delete_timeline_for_owner(timeline.id, owner.id)

    assert db.session.get(Task, task.task_id) is None
    assert db.session.get(Task, child_task.task_id) is None
    assert db.session.get(Timeline, timeline.id) is None


def test_trash_service_owner_guard_raises_not_found(app):
    owner = _create_user("trash-service-guard-owner@example.com", "trash_service_guard_owner")
    outsider = _create_user("trash-service-guard-outsider@example.com", "trash_service_guard_outsider")

    task = Task(
        user_id=owner.id,
        name="guard task",
        deleted_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    timeline = Timeline(
        user_id=owner.id,
        name="guard timeline",
        deleted_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.session.add_all([task, timeline])
    db.session.commit()

    with pytest.raises(TrashOperationError) as task_exc:
        restore_task_for_owner(task.task_id, outsider.id)
    assert task_exc.value.status_code == 404

    with pytest.raises(TrashOperationError) as timeline_exc:
        permanently_delete_timeline_for_owner(timeline.id, outsider.id)
    assert timeline_exc.value.status_code == 404
