from datetime import datetime, timedelta, timezone
from io import BytesIO
import os

import pytest
from werkzeug.datastructures import FileStorage

from models import db
from models.notification import Notification
from models.subtask import Subtask
from models.task import Task
from models.task_comment import TaskComment
from models.task_user import TaskUser
from models.timeline import TaskFile, Timeline
from models.timeline_user import TimelineUser
from models.user import User
from services.task_service import (
    TaskOperationError,
    add_task_comment_for_member,
    add_task_member_for_operator,
    can_manage_task_members,
    create_task_for_user,
    create_notification,
    create_subtask_for_task,
    delete_subtask_for_task,
    delete_task_file_for_user,
    find_unknown_fields as task_find_unknown_fields,
    get_user_task_role,
    list_subtasks_for_task,
    list_task_comments_for_member,
    list_task_files_for_member,
    list_tasks_for_user,
    list_upcoming_tasks_for_user,
    remove_task_member_for_owner,
    resolve_task_file_download_for_user,
    soft_delete_task_for_owner,
    soft_delete_task_comment_for_user,
    summarize_task_comments_for_member,
    toggle_task_for_member,
    toggle_subtask_for_task,
    update_subtask_for_task,
    update_task_member_role_for_operator,
    update_task_status_for_member,
    update_task_for_member,
    upload_task_file_for_member,
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


def _create_timeline(owner_id: int, name: str = "Task Service Timeline") -> Timeline:
    timeline = Timeline(user_id=owner_id, name=name)
    db.session.add(timeline)
    db.session.flush()
    db.session.add(TimelineUser(timeline_id=timeline.id, user_id=owner_id, role=0))
    db.session.commit()
    return timeline


def test_create_task_for_user_validates_payload_and_dates(app):
    owner = _create_user("task-create-validation@example.com", "task_create_validation")

    with pytest.raises(TaskOperationError) as unknown_exc:
        create_task_for_user(
            owner.id,
            {
                "name": "Task with junk field",
                "end_date": "2026-04-20T18:00:00",
                "junk": True,
            },
        )
    assert unknown_exc.value.status_code == 400

    with pytest.raises(TaskOperationError) as status_exc:
        create_task_for_user(
            owner.id,
            {
                "name": "Bad status task",
                "end_date": "2026-04-20T18:00:00",
                "status": "not_a_real_status",
            },
        )
    assert status_exc.value.status_code == 400

    with pytest.raises(TaskOperationError) as priority_type_exc:
        create_task_for_user(
            owner.id,
            {
                "name": "Bad priority type",
                "end_date": "2026-04-20T18:00:00",
                "priority": "high",
            },
        )
    assert priority_type_exc.value.status_code == 400

    with pytest.raises(TaskOperationError) as priority_range_exc:
        create_task_for_user(
            owner.id,
            {
                "name": "Bad priority range",
                "end_date": "2026-04-20T18:00:00",
                "priority": 9,
            },
        )
    assert priority_range_exc.value.status_code == 400

    with pytest.raises(TaskOperationError) as start_date_exc:
        create_task_for_user(
            owner.id,
            {
                "name": "Bad start date",
                "start_date": "not-a-date",
                "end_date": "2026-04-20T18:00:00",
            },
        )
    assert start_date_exc.value.status_code == 400

    with pytest.raises(TaskOperationError) as end_date_exc:
        create_task_for_user(
            owner.id,
            {
                "name": "Bad end date",
                "end_date": "not-a-date",
            },
        )
    assert end_date_exc.value.status_code == 400


def test_update_task_for_member_validates_and_persists_fields(app):
    owner = _create_user("task-update-validation@example.com", "task_update_validation")
    task_id = create_task_for_user(
        owner.id,
        {
            "name": "Update target",
            "end_date": "2026-04-20T18:00:00",
        },
    )

    update_task_for_member(
        task_id,
        {
            "name": "Updated task name",
            "priority": 3,
            "status": "in_progress",
            "estimated_hours": 8,
            "start_date": "2026-04-01T10:00:00",
        },
    )
    task = db.session.get(Task, task_id)
    assert task is not None
    assert task.name == "Updated task name"
    assert task.priority == 3
    assert task.status == "in_progress"
    assert task.estimated_hours == 8

    with pytest.raises(TaskOperationError) as empty_name_exc:
        update_task_for_member(task_id, {"name": "   "})
    assert empty_name_exc.value.status_code == 400

    with pytest.raises(TaskOperationError) as bad_status_exc:
        update_task_for_member(task_id, {"status": "not_a_real_status"})
    assert bad_status_exc.value.status_code == 400


def test_list_tasks_for_user_includes_assigned_tasks_and_owner_flag(app):
    owner = _create_user("task-list-owner-service@example.com", "task_list_owner_service")
    member = _create_user("task-list-member-service@example.com", "task_list_member_service")

    task_id = create_task_for_user(
        owner.id,
        {
            "name": "Assigned task",
            "end_date": "2026-04-20T18:00:00",
        },
    )
    db.session.add(TaskUser(task_id=task_id, user_id=member.id, role=1))
    db.session.commit()

    payload = list_tasks_for_user(member.id)
    assigned = next(item for item in payload if item["task_id"] == task_id)
    assert assigned["name"] == "Assigned task"
    assert assigned["is_owner"] is False


def test_toggle_task_for_member_updates_completed_and_status(app):
    owner = _create_user("task-toggle-service@example.com", "task_toggle_service")
    task_id = create_task_for_user(
        owner.id,
        {
            "name": "Toggle target",
            "end_date": "2026-04-20T18:00:00",
        },
    )

    completed = toggle_task_for_member(task_id)
    task = db.session.get(Task, task_id)

    assert completed is True
    assert task is not None
    assert task.completed is True
    assert task.status == "completed"


def test_list_upcoming_tasks_for_user_includes_due_and_progress_items(app):
    user = _create_user("task-upcoming-service@example.com", "task_upcoming_service")
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    due_soon = Task(
        user_id=user.id,
        name="due soon",
        completed=False,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=2),
    )
    progress_warn = Task(
        user_id=user.id,
        name="progress warning",
        completed=False,
        start_date=now - timedelta(days=40),
        end_date=now + timedelta(days=10),
    )
    far_future = Task(
        user_id=user.id,
        name="not upcoming",
        completed=False,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=30),
    )
    db.session.add_all([due_soon, progress_warn, far_future])
    db.session.commit()

    names = {item["name"] for item in list_upcoming_tasks_for_user(user.id)}

    assert "due soon" in names
    assert "progress warning" in names
    assert "not upcoming" not in names


def test_soft_delete_task_for_owner_marks_deleted_at(app):
    owner = _create_user("task-soft-delete-service@example.com", "task_soft_delete_service")
    task_id = create_task_for_user(
        owner.id,
        {
            "name": "Delete me",
            "end_date": "2026-04-22T12:00:00",
        },
    )

    soft_delete_task_for_owner(task_id)
    deleted_task = db.session.get(Task, task_id)

    assert deleted_task is not None
    assert deleted_task.deleted_at is not None


def test_create_task_for_user_accepts_timeline_owner_membership(app):
    owner = _create_user("task-timeline-owner-service@example.com", "task_timeline_owner_service")
    timeline = _create_timeline(owner.id)

    task_id = create_task_for_user(
        owner.id,
        {
            "name": "Timeline task",
            "timeline_id": timeline.id,
            "end_date": "2026-04-20T18:00:00",
        },
    )

    owner_member = TaskUser.query.filter_by(task_id=task_id, user_id=owner.id).first()
    assert owner_member is not None
    assert owner_member.role == 0


def test_task_service_find_unknown_fields_sorted():
    unknown = task_find_unknown_fields(
        {"name": "Task", "priority": 2, "x": 1, "a": 2},
        {"name", "priority"},
    )
    assert unknown == ["a", "x"]


def test_task_service_create_notification_persists_data(app):
    user = _create_user("task-notif@example.com", "task_notif_user")

    create_notification(
        user_id=user.id,
        ntype="task_assigned",
        title="Assigned",
        content="A new task",
        link="/tasks/1",
    )
    db.session.commit()

    notif = Notification.query.filter_by(user_id=user.id, title="Assigned").first()
    assert notif is not None
    assert notif.type == "task_assigned"


def test_get_user_task_role_prefers_task_role_over_timeline_role(app):
    owner = _create_user("task-role-owner@example.com", "task_role_owner")
    member = _create_user("task-role-member@example.com", "task_role_member")

    timeline = _create_timeline(owner.id, "Task Role Timeline")
    task = Task(user_id=owner.id, name="Task Role Task", timeline_id=timeline.id)
    db.session.add(task)
    db.session.commit()

    db.session.add(TimelineUser(timeline_id=timeline.id, user_id=member.id, role=0))
    db.session.add(TaskUser(task_id=task.task_id, user_id=member.id, role=1))
    db.session.commit()

    role = get_user_task_role(member.id, task.task_id)
    assert role == 1


def test_get_user_task_role_falls_back_to_timeline_role(app):
    owner = _create_user("task-fallback-owner@example.com", "task_fallback_owner")
    member = _create_user("task-fallback-member@example.com", "task_fallback_member")

    timeline = _create_timeline(owner.id, "Fallback Timeline")
    task = Task(user_id=owner.id, name="Fallback Task", timeline_id=timeline.id)
    db.session.add(task)
    db.session.commit()

    db.session.add(TimelineUser(timeline_id=timeline.id, user_id=member.id, role=1))
    db.session.commit()

    role = get_user_task_role(member.id, task.task_id)
    assert role == 1


def test_can_manage_task_members_owner_and_timeline_owner(app):
    owner = _create_user("manage-owner@example.com", "manage_owner")
    timeline_owner = _create_user("manage-timeline-owner@example.com", "manage_timeline_owner")
    collaborator = _create_user("manage-collab@example.com", "manage_collab")

    timeline = _create_timeline(owner.id, "Manage Timeline")
    task = Task(user_id=owner.id, name="Manage Task", timeline_id=timeline.id)
    db.session.add(task)
    db.session.commit()

    db.session.add(TaskUser(task_id=task.task_id, user_id=owner.id, role=0))
    db.session.add(TimelineUser(timeline_id=timeline.id, user_id=timeline_owner.id, role=0))
    db.session.add(TaskUser(task_id=task.task_id, user_id=collaborator.id, role=1))
    db.session.commit()

    assert can_manage_task_members(owner.id, task) is True
    assert can_manage_task_members(timeline_owner.id, task) is True
    assert can_manage_task_members(collaborator.id, task) is False


def test_task_service_member_management_operations(app):
    owner = _create_user("task-member-op-owner@example.com", "task_member_op_owner")
    member = _create_user("task-member-op-member@example.com", "task_member_op_member")
    outsider = _create_user("task-member-op-outsider@example.com", "task_member_op_outsider")

    timeline = _create_timeline(owner.id, "Task Member Ops Timeline")
    db.session.add(TimelineUser(timeline_id=timeline.id, user_id=member.id, role=1))
    task = Task(user_id=owner.id, timeline_id=timeline.id, name="Task Member Ops")
    db.session.add(task)
    db.session.flush()
    db.session.add(TaskUser(task_id=task.task_id, user_id=owner.id, role=0))
    db.session.commit()

    add_task_member_for_operator(task.task_id, owner.id, member.id, role=1)
    added_member = TaskUser.query.filter_by(task_id=task.task_id, user_id=member.id).first()
    assert added_member is not None
    assert added_member.role == 1

    with pytest.raises(TaskOperationError) as duplicate_exc:
        add_task_member_for_operator(task.task_id, owner.id, member.id, role=1)
    assert duplicate_exc.value.status_code == 409

    with pytest.raises(TaskOperationError) as permission_exc:
        add_task_member_for_operator(task.task_id, outsider.id, owner.id, role=1)
    assert permission_exc.value.status_code == 403

    remove_task_member_for_owner(task.task_id, member.id)
    assert TaskUser.query.filter_by(task_id=task.task_id, user_id=member.id).first() is None

    update_task_member_role_for_operator(task.task_id, member.id, 0, owner.id)
    promoted_member = TaskUser.query.filter_by(task_id=task.task_id, user_id=member.id).first()
    owner_member = TaskUser.query.filter_by(task_id=task.task_id, user_id=owner.id).first()
    assert promoted_member is not None
    assert promoted_member.role == 0
    assert owner_member is not None
    assert owner_member.role == 1

    with pytest.raises(TaskOperationError) as demote_owner_exc:
        update_task_member_role_for_operator(task.task_id, member.id, 1, owner.id)
    assert demote_owner_exc.value.status_code == 400

    with pytest.raises(TaskOperationError) as remove_owner_exc:
        remove_task_member_for_owner(task.task_id, member.id)
    assert remove_owner_exc.value.status_code == 400


def test_create_task_for_user_accepts_assignee_user_ids(app):
    owner = _create_user("task-create-owner@example.com", "task_create_owner")
    member = _create_user("task-create-member@example.com", "task_create_member")
    outsider = _create_user("task-create-outsider@example.com", "task_create_outsider")

    timeline = _create_timeline(owner.id, "Task Create Timeline")
    db.session.add(TimelineUser(timeline_id=timeline.id, user_id=member.id, role=1))
    db.session.commit()

    task_id = create_task_for_user(
        user_id=owner.id,
        data={
            "name": "可直接指派的任務",
            "timeline_id": timeline.id,
            "end_date": "2026-04-25",
            "assignee_user_ids": [member.id, owner.id, member.id],
        },
    )

    task_members = TaskUser.query.filter_by(task_id=task_id).all()
    member_roles = {item.user_id: item.role for item in task_members}
    assert member_roles[owner.id] == 0
    assert member_roles[member.id] == 1
    assert len(task_members) == 2

    with pytest.raises(TaskOperationError) as invalid_assignee_exc:
        create_task_for_user(
            user_id=owner.id,
            data={
                "name": "非法指派任務",
                "timeline_id": timeline.id,
                "end_date": "2026-04-27",
                "assignee_user_ids": [outsider.id],
            },
        )
    assert invalid_assignee_exc.value.status_code == 400


def test_task_service_validates_depends_on_task_ids(app):
    owner = _create_user("task-depends-owner@example.com", "task_depends_owner")

    main_timeline = _create_timeline(owner.id, "Task Depends Timeline")
    other_timeline = _create_timeline(owner.id, "Task Depends Other Timeline")
    base_task = Task(
        user_id=owner.id,
        timeline_id=main_timeline.id,
        name="既有前置任務",
        end_date=datetime(2026, 4, 20),
    )
    foreign_task = Task(
        user_id=owner.id,
        timeline_id=other_timeline.id,
        name="其他專案任務",
        end_date=datetime(2026, 4, 20),
    )
    db.session.add_all([base_task, foreign_task])
    db.session.commit()

    task_id = create_task_for_user(
        user_id=owner.id,
        data={
            "name": "需前置依賴的任務",
            "timeline_id": main_timeline.id,
            "end_date": "2026-04-25",
            "depends_on_task_ids": [base_task.task_id, base_task.task_id],
        },
    )
    created_task = db.session.get(Task, task_id)
    assert created_task is not None
    assert created_task.depends_on_task_ids == [base_task.task_id]

    with pytest.raises(TaskOperationError) as missing_timeline_exc:
        create_task_for_user(
            user_id=owner.id,
            data={
                "name": "沒有專案但有依賴",
                "end_date": "2026-04-26",
                "depends_on_task_ids": [base_task.task_id],
            },
        )
    assert missing_timeline_exc.value.status_code == 400

    with pytest.raises(TaskOperationError) as cross_timeline_exc:
        create_task_for_user(
            user_id=owner.id,
            data={
                "name": "跨專案依賴",
                "timeline_id": main_timeline.id,
                "end_date": "2026-04-26",
                "depends_on_task_ids": [foreign_task.task_id],
            },
        )
    assert cross_timeline_exc.value.status_code == 400

    with pytest.raises(TaskOperationError) as self_dependency_exc:
        update_task_for_member(task_id, {"depends_on_task_ids": [task_id]})
    assert self_dependency_exc.value.status_code == 400

    update_task_for_member(task_id, {"depends_on_task_ids": [base_task.task_id]})
    refreshed_task = db.session.get(Task, task_id)
    assert refreshed_task is not None
    assert refreshed_task.depends_on_task_ids == [base_task.task_id]


def test_task_service_comment_operations(app):
    owner = _create_user("task-comment-op-owner@example.com", "task_comment_op_owner")
    member = _create_user("task-comment-op-member@example.com", "task_comment_op_member")

    task = Task(user_id=owner.id, name="Task Comment Ops")
    db.session.add(task)
    db.session.commit()

    payload = add_task_comment_for_member(task.task_id, owner.id, {"message": "first comment"})
    comment_id = payload["comment_id"]

    comments = list_task_comments_for_member(task.task_id)
    assert len(comments) == 1
    assert comments[0]["comment_id"] == comment_id

    with pytest.raises(TaskOperationError) as missing_message_exc:
        add_task_comment_for_member(task.task_id, owner.id, {"message": ""})
    assert missing_message_exc.value.status_code == 400

    with pytest.raises(TaskOperationError) as forbidden_exc:
        soft_delete_task_comment_for_user(task.task_id, comment_id, member.id)
    assert forbidden_exc.value.status_code == 403

    soft_delete_task_comment_for_user(task.task_id, comment_id, owner.id)
    deleted_comment = db.session.get(TaskComment, comment_id)
    assert deleted_comment is not None
    assert deleted_comment.deleted_at is not None

    with pytest.raises(TaskOperationError) as not_found_exc:
        soft_delete_task_comment_for_user(task.task_id, comment_id, owner.id)
    assert not_found_exc.value.status_code == 404


def test_task_service_subtask_and_status_operations(app):
    owner = _create_user("task-subtask-op-owner@example.com", "task_subtask_op_owner")

    task = Task(user_id=owner.id, name="Task Subtask Ops", status="pending", completed=False)
    db.session.add(task)
    db.session.commit()

    with pytest.raises(TaskOperationError) as missing_name_exc:
        create_subtask_for_task(task.task_id, "")
    assert missing_name_exc.value.status_code == 400

    created = create_subtask_for_task(task.task_id, "Subtask 1")
    subtask_id = created["id"]

    listed = list_subtasks_for_task(task.task_id)
    assert len(listed) == 1
    assert listed[0]["id"] == subtask_id

    updated = update_subtask_for_task(
        task.task_id,
        subtask_id,
        {"name": "Subtask 1 Updated", "completed": True, "sort_order": 5},
    )
    assert updated["name"] == "Subtask 1 Updated"
    assert updated["completed"] is True
    assert updated["sort_order"] == 5

    toggled = toggle_subtask_for_task(task.task_id, subtask_id)
    assert toggled["completed"] is False

    status_payload = update_task_status_for_member(task.task_id, "completed")
    assert status_payload["status"] == "completed"
    assert status_payload["completed"] is True

    refreshed_task = db.session.get(Task, task.task_id)
    assert refreshed_task is not None
    assert refreshed_task.status == "completed"
    assert refreshed_task.completed is True

    with pytest.raises(TaskOperationError) as invalid_status_exc:
        update_task_status_for_member(task.task_id, "bad")
    assert invalid_status_exc.value.status_code == 400

    delete_subtask_for_task(task.task_id, subtask_id)
    assert db.session.get(Subtask, subtask_id) is None

    with pytest.raises(TaskOperationError) as missing_subtask_exc:
        toggle_subtask_for_task(task.task_id, subtask_id)
    assert missing_subtask_exc.value.status_code == 404

    with pytest.raises(TaskOperationError) as missing_task_exc:
        update_task_status_for_member(999999, "pending")
    assert missing_task_exc.value.status_code == 404


def test_task_service_summary_orchestration(app, monkeypatch):
    owner = _create_user("task-summary-service-owner@example.com", "task_summary_service_owner")
    task = Task(user_id=owner.id, name="Task Summary Service")
    db.session.add(task)
    db.session.commit()

    empty_payload = summarize_task_comments_for_member(task.task_id)
    assert empty_payload["summary"]["decisions"] == []
    assert empty_payload["meta"]["comment_count"] == 0

    db.session.add(TaskComment(task_id=task.task_id, user_id=owner.id, task_message="summary comment"))
    db.session.commit()

    def _fake_summary(_task, comment_items):
        assert len(comment_items) == 1
        return (
            {
                "decisions": ["使用 service 統一流程"],
                "risks": ["需要補更多回歸測試"],
                "next_actions": ["補上整合測試"],
            },
            {
                "total_comments": 1,
                "used_comments": 1,
                "truncated": False,
                "context_chars": 100,
                "model": "test-model",
            },
        )

    monkeypatch.setattr("services.task_service.generate_task_comment_summary", _fake_summary)
    payload = summarize_task_comments_for_member(task.task_id)
    assert payload["summary"]["decisions"][0] == "使用 service 統一流程"
    assert payload["meta"]["model"] == "test-model"

    def _raise_runtime(*_args, **_kwargs):
        raise RuntimeError("AI 摘要服務暫時不可用，請稍後再試")

    monkeypatch.setattr("services.task_service.generate_task_comment_summary", _raise_runtime)
    with pytest.raises(TaskOperationError) as runtime_exc:
        summarize_task_comments_for_member(task.task_id)
    assert runtime_exc.value.status_code == 503

    with pytest.raises(TaskOperationError) as not_found_exc:
        summarize_task_comments_for_member(999999)
    assert not_found_exc.value.status_code == 404


def test_task_service_file_operations_and_validation(app):
    owner = _create_user("task-file-service-owner@example.com", "task_file_service_owner")
    member = _create_user("task-file-service-member@example.com", "task_file_service_member")
    outsider = _create_user("task-file-service-outsider@example.com", "task_file_service_outsider")

    task = Task(user_id=owner.id, name="Task File Service")
    db.session.add(task)
    db.session.flush()
    db.session.add(TaskUser(task_id=task.task_id, user_id=owner.id, role=0))
    db.session.add(TaskUser(task_id=task.task_id, user_id=member.id, role=1))
    db.session.commit()

    uploaded = upload_task_file_for_member(
        task.task_id,
        member.id,
        FileStorage(stream=BytesIO(b"hello"), filename="report.txt"),
    )
    file_id = uploaded["id"]
    stored_filename = uploaded["filename"]
    stored_path = db.session.get(TaskFile, file_id).file_path
    assert os.path.exists(stored_path)

    listed = list_task_files_for_member(task.task_id)
    assert any(item["id"] == file_id for item in listed)

    folder, safe_name, original_name = resolve_task_file_download_for_user(stored_filename, member.id)
    assert safe_name == stored_filename
    assert original_name == "report.txt"
    assert folder

    with pytest.raises(TaskOperationError) as forbidden_download_exc:
        resolve_task_file_download_for_user(stored_filename, outsider.id)
    assert forbidden_download_exc.value.status_code == 403

    with pytest.raises(TaskOperationError) as bad_ext_exc:
        upload_task_file_for_member(
            task.task_id,
            owner.id,
            FileStorage(stream=BytesIO(b"bad"), filename="bad.exe"),
        )
    assert bad_ext_exc.value.status_code == 400

    with pytest.raises(TaskOperationError) as too_large_exc:
        upload_task_file_for_member(
            task.task_id,
            owner.id,
            FileStorage(stream=BytesIO(b"a" * (10 * 1024 * 1024 + 1)), filename="big.txt"),
        )
    assert too_large_exc.value.status_code == 400

    with pytest.raises(TaskOperationError) as forbidden_delete_exc:
        delete_task_file_for_user(task.task_id, file_id, outsider.id)
    assert forbidden_delete_exc.value.status_code == 403

    delete_task_file_for_user(task.task_id, file_id, owner.id)
    assert db.session.get(TaskFile, file_id) is None
    assert not os.path.exists(stored_path)

