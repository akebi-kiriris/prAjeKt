from datetime import date, datetime, timezone
from io import BytesIO
from types import SimpleNamespace

import pytest
from werkzeug.datastructures import FileStorage

from models import db
from models.group import Group, GroupMember
from models.message import Message, MessageRead
from models.notification import Notification
from models.subtask import Subtask
from models.task import Task
from models.task_comment import TaskComment
from models.task_user import TaskUser
from models.timeline import TaskFile, Timeline
from models.timeline_user import TimelineUser
from models.todo import Todo
from models.user import User
from services.auth_service import (
    AuthOperationError,
    auth_user_to_dict,
    authenticate_user,
    current_user_to_dict,
    get_current_user_or_404,
    register_user,
)
from services.group_service import (
    GroupOperationError,
    create_group_for_user,
    generate_unique_invite_code,
    group_member_to_dict,
    group_message_to_dict,
    group_room_name,
    group_to_dict,
    is_group_member,
    join_group_by_invite_code,
    leave_group_for_user,
    list_group_members_payload,
    list_group_messages_for_member,
    list_groups_for_user,
    send_group_message_for_member,
)
from services.message_service import (
    create_group_message,
    get_unread_message_count,
    get_unread_messages_query,
    mark_all_unread_messages_as_read,
    serialize_group_message,
)
from services.notification_service import (
    NotificationOperationError,
    delete_notification_for_user,
    get_notifications_for_user,
    get_unread_count_for_user,
    mark_all_notifications_as_read,
    mark_notification_as_read,
    notification_to_dict,
)
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
from services.task_service import (
    TaskOperationError,
    add_task_comment_for_member,
    add_task_member_for_operator,
    build_task_member_list,
    can_manage_task_members,
    create_subtask_for_task,
    create_notification,
    delete_task_file_for_user,
    delete_subtask_for_task,
    find_unknown_fields as task_find_unknown_fields,
    get_user_task_role,
    list_subtasks_for_task,
    list_task_files_for_member,
    list_task_comments_for_member,
    remove_task_member_for_owner,
    require_task_role,
    resolve_task_file_download_for_user,
    soft_delete_task_comment_for_user,
    summarize_task_comments_for_member,
    task_comment_to_dict,
    task_list_item_to_dict,
    task_member_to_dict,
    toggle_subtask_for_task,
    upload_task_file_for_member,
    update_subtask_for_task,
    update_task_member_role_for_operator,
    update_task_status_for_member,
)
from services.trash_service import (
    TrashOperationError,
    get_trash_payload,
    permanently_delete_task_for_owner,
    permanently_delete_timeline_for_owner,
    restore_task_for_owner,
    restore_timeline_for_owner,
)
from services.timeline_service import (
    TimelineAIGenerationError,
    find_unknown_fields as timeline_find_unknown_fields,
    generate_timeline_tasks_with_ai,
    get_task_access,
    get_user_timeline_role,
    require_timeline_role,
    timeline_list_item_to_dict,
    timeline_member_item_to_dict,
    timeline_task_item_to_dict,
)
import services.timeline_service as timeline_service_module
from services.todo_service import (
    TodoOperationError,
    create_todo_for_user,
    find_unknown_fields as todo_find_unknown_fields,
    list_todos_for_user,
    soft_delete_todo_for_user,
    todo_to_dict,
    toggle_todo_for_user,
    update_todo_for_user,
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


def test_auth_service_serializers(app):
    user = _create_user("auth-service@example.com", "auth_service_user")
    user.phone = "0912345678"
    db.session.commit()

    auth_payload = auth_user_to_dict(user)
    current_payload = current_user_to_dict(user)

    assert auth_payload == {
        "id": user.id,
        "name": user.name,
        "username": user.username,
        "email": user.email,
    }
    assert current_payload["phone"] == "0912345678"


def test_auth_service_operations_and_errors(app):
    user_id = register_user(
        {
            "name": "Auth Ops",
            "username": "auth_ops_user",
            "email": "auth-ops@example.com",
            "password": "Password123!",
            "phone": "0912000111",
        }
    )

    user = db.session.get(User, user_id)
    assert user is not None
    assert user.email == "auth-ops@example.com"

    authenticated = authenticate_user("auth-ops@example.com", "Password123!")
    assert authenticated.id == user_id

    loaded = get_current_user_or_404(user_id)
    assert loaded.id == user_id

    with pytest.raises(AuthOperationError) as duplicate_exc:
        register_user(
            {
                "name": "Another",
                "username": "auth_ops_user_2",
                "email": "auth-ops@example.com",
                "password": "Password123!",
            }
        )
    assert duplicate_exc.value.status_code == 409

    with pytest.raises(AuthOperationError) as missing_exc:
        register_user({"name": "Missing Password", "email": "missing-auth@example.com"})
    assert missing_exc.value.status_code == 400

    with pytest.raises(AuthOperationError) as wrong_password_exc:
        authenticate_user("auth-ops@example.com", "WrongPassword")
    assert wrong_password_exc.value.status_code == 401

    with pytest.raises(AuthOperationError) as not_found_exc:
        get_current_user_or_404(999999)
    assert not_found_exc.value.status_code == 404


def test_profile_service_helpers_and_serializers(app):
    unknown = profile_find_unknown_fields(
        {"name": "A", "x": 1, "z": 2},
        {"name", "email"},
    )
    assert unknown == ["x", "z"]

    user = _create_user("profile-service@example.com", "profile_service_user")
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


def test_profile_service_update_search_and_chart_stats(app):
    user = _create_user("profile-service-ops@example.com", "profile_service_ops")
    target = _create_user("profile-service-target@example.com", "profile_service_target")

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


def test_profile_service_validation_errors(app):
    owner = _create_user("profile-service-owner@example.com", "profile_service_owner")
    duplicate = _create_user("profile-service-dup@example.com", "profile_service_dup")

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


def test_notification_service_to_dict(app):
    user = _create_user("notif-service@example.com", "notif_service_user")
    notif = Notification(
        user_id=user.id,
        type="task_assigned",
        title="Assigned",
        content="You have a new task",
        link="/tasks/1",
        is_read=False,
    )
    db.session.add(notif)
    db.session.commit()

    payload = notification_to_dict(notif)
    assert payload["title"] == "Assigned"
    assert payload["is_read"] is False
    assert payload["created_at"].endswith("Z")


def test_notification_service_operations(app):
    user = _create_user("notif-ops@example.com", "notif_ops_user")
    n1 = Notification(
        user_id=user.id,
        type="task_assigned",
        title="n1",
        content="A",
        link="/tasks/1",
        is_read=False,
    )
    n2 = Notification(
        user_id=user.id,
        type="task_assigned",
        title="n2",
        content="B",
        link="/tasks/2",
        is_read=False,
    )
    db.session.add_all([n1, n2])
    db.session.commit()

    notifications = get_notifications_for_user(user.id)
    assert len(notifications) == 2
    assert get_unread_count_for_user(user.id) == 2

    mark_notification_as_read(n1.id, user.id)
    assert get_unread_count_for_user(user.id) == 1

    mark_all_notifications_as_read(user.id)
    assert get_unread_count_for_user(user.id) == 0

    delete_notification_for_user(n2.id, user.id)
    assert Notification.query.filter_by(id=n2.id).first() is None


def test_notification_service_not_found_errors(app):
    user = _create_user("notif-err@example.com", "notif_err_user")

    with pytest.raises(NotificationOperationError) as read_exc:
        mark_notification_as_read(999999, user.id)
    assert read_exc.value.status_code == 404

    with pytest.raises(NotificationOperationError) as delete_exc:
        delete_notification_for_user(999999, user.id)
    assert delete_exc.value.status_code == 404


def test_todo_service_helpers_and_serializer(app):
    unknown = todo_find_unknown_fields(
        {"title": "t", "content": "c", "bad": True},
        {"title", "content"},
    )
    assert unknown == ["bad"]

    user = _create_user("todo-service@example.com", "todo_service_user")
    todo = Todo(
        user_id=user.id,
        title="Todo title",
        content="Todo content",
        type="personal",
        priority=2,
    )
    db.session.add(todo)
    db.session.commit()

    payload = todo_to_dict(todo)
    assert payload["title"] == "Todo title"
    assert payload["priority"] == 2
    assert payload["created_at"].endswith("Z")


def test_todo_service_crud_operations(app):
    user = _create_user("todo-service-crud@example.com", "todo_service_crud_user")

    todo_id = create_todo_for_user(
        user.id,
        {
            "title": "Plan Sprint",
            "content": "Prepare sprint goals",
            "priority": 1,
            "deadline": "2026-04-30",
        },
    )

    listed = list_todos_for_user(user.id)
    assert any(item.id == todo_id for item in listed)

    update_todo_for_user(
        todo_id,
        user.id,
        {
            "title": "Plan Sprint Updated",
            "completed": True,
            "priority": 2,
        },
    )
    updated = db.session.get(Todo, todo_id)
    assert updated.title == "Plan Sprint Updated"
    assert updated.completed is True

    completed = toggle_todo_for_user(todo_id, user.id)
    assert completed is False

    soft_delete_todo_for_user(todo_id, user.id)
    assert db.session.get(Todo, todo_id).deleted_at is not None


def test_todo_service_validation_and_not_found_errors(app):
    user = _create_user("todo-service-error@example.com", "todo_service_error_user")

    with pytest.raises(TodoOperationError) as unknown_exc:
        create_todo_for_user(
            user.id,
            {
                "title": "A",
                "content": "B",
                "not_allowed": True,
            },
        )
    assert unknown_exc.value.status_code == 400

    todo_id = create_todo_for_user(
        user.id,
        {
            "title": "Valid",
            "content": "Valid content",
        },
    )

    with pytest.raises(TodoOperationError) as priority_exc:
        update_todo_for_user(todo_id, user.id, {"priority": 9})
    assert priority_exc.value.status_code == 400

    with pytest.raises(TodoOperationError) as missing_exc:
        update_todo_for_user(999999, user.id, {"title": "X"})
    assert missing_exc.value.status_code == 404


def test_group_service_generate_unique_invite_code_skips_existing(app, monkeypatch):
    owner = _create_user("group-owner@example.com", "group_owner")
    existing = Group(
        group_name="Existing Group",
        group_type="task",
        group_inviteCode="111111",
        created_by=owner.id,
    )
    db.session.add(existing)
    db.session.commit()

    values = iter([111111, 111111, 222222])
    monkeypatch.setattr("services.group_service.random.randint", lambda _a, _b: next(values))

    code = generate_unique_invite_code()

    assert code == "222222"
    assert len(code) == 6


def test_group_service_serializers_and_membership(app):
    owner = _create_user("group-owner2@example.com", "group_owner2")
    member = _create_user("group-member2@example.com", "group_member2")

    group = Group(
        group_name="Service Group",
        group_type="task",
        group_inviteCode="123456",
        created_by=owner.id,
    )
    db.session.add(group)
    db.session.commit()

    gm = GroupMember(group_id=group.group_id, user_id=member.id)
    db.session.add(gm)
    db.session.commit()

    group_payload = group_to_dict(group)
    member_payload = group_member_to_dict(member)
    msg_payload = group_message_to_dict(
        type("GroupMsg", (), {"message_id": 1, "content": "hi", "sender_name": "A", "created_at": datetime.now(timezone.utc)})
    )

    assert group_payload["invite_code"] == "123456"
    assert group_payload["created_at"].endswith("Z")
    assert member_payload["email"] == member.email
    assert msg_payload["created_at"].endswith("Z")
    assert is_group_member(group.group_id, member.id) is True
    assert is_group_member(group.group_id, owner.id) is False
    assert group_room_name(group.group_id) == f"group_{group.group_id}"


def test_group_service_operations_and_errors(app):
    owner = _create_user("group-service-owner@example.com", "group_service_owner")
    member = _create_user("group-service-member@example.com", "group_service_member")
    outsider = _create_user("group-service-outsider@example.com", "group_service_outsider")

    created = create_group_for_user(owner.id, "Service Ops Group")
    group_id = created["group_id"]
    invite_code = created["invite_code"]

    owner_groups = list_groups_for_user(owner.id)
    assert any(group["group_id"] == group_id for group in owner_groups)

    join_group_by_invite_code(member.id, invite_code)
    assert is_group_member(group_id, member.id) is True

    members = list_group_members_payload(group_id)
    member_ids = {item["user_id"] for item in members}
    assert owner.id in member_ids
    assert member.id in member_ids

    message_id = send_group_message_for_member(group_id, owner.id, "hello service group")
    assert isinstance(message_id, int)

    messages = list_group_messages_for_member(group_id, owner.id)
    assert any(item["content"] == "hello service group" for item in messages)

    leave_group_for_user(group_id, member.id)
    assert is_group_member(group_id, member.id) is False

    with pytest.raises(GroupOperationError) as invalid_code_exc:
        join_group_by_invite_code(outsider.id, "badcode")
    assert invalid_code_exc.value.status_code == 404

    with pytest.raises(GroupOperationError) as duplicate_join_exc:
        join_group_by_invite_code(owner.id, invite_code)
    assert duplicate_join_exc.value.status_code == 409

    with pytest.raises(GroupOperationError) as message_forbidden_exc:
        list_group_messages_for_member(group_id, outsider.id)
    assert message_forbidden_exc.value.status_code == 403

    with pytest.raises(GroupOperationError) as message_empty_exc:
        send_group_message_for_member(group_id, owner.id, "   ")
    assert message_empty_exc.value.status_code == 400

    with pytest.raises(GroupOperationError) as leave_missing_exc:
        leave_group_for_user(group_id, outsider.id)
    assert leave_missing_exc.value.status_code == 404


def test_message_service_create_and_serialize(app):
    sender = _create_user("message-sender@example.com", "message_sender")

    payload = create_group_message(group_id=99, sender_id=sender.id, content="hello world")

    assert payload["sender_id"] == sender.id
    assert payload["content"] == "hello world"
    assert payload["sender_name"] == sender.name
    assert payload["created_at"].endswith("Z")



def test_message_service_create_group_message_user_missing(app):
    with pytest.raises(ValueError):
        create_group_message(group_id=1, sender_id=99999, content="fail")


def test_message_service_get_unread_messages_query(app):
    user = _create_user("message-unread@example.com", "message_unread_user")

    unread = Message(group_id=1, sender_id=user.id, content="unread")
    read = Message(group_id=1, sender_id=user.id, content="read")
    db.session.add_all([unread, read])
    db.session.commit()

    db.session.add(MessageRead(message_id=read.message_id, user_id=user.id))
    db.session.commit()

    results = get_unread_messages_query(user.id).all()
    unread_ids = {row.message_id for row in results}

    assert unread.message_id in unread_ids
    assert read.message_id not in unread_ids


def test_message_service_unread_count_and_mark_all_read(app):
    user = _create_user("message-mark-all@example.com", "message_mark_all_user")
    sender = _create_user("message-mark-all-sender@example.com", "message_mark_all_sender")

    read_message = Message(group_id=1, sender_id=sender.id, content="read")
    unread_message_a = Message(group_id=1, sender_id=sender.id, content="unread a")
    unread_message_b = Message(group_id=1, sender_id=sender.id, content="unread b")
    db.session.add_all([read_message, unread_message_a, unread_message_b])
    db.session.flush()

    db.session.add(MessageRead(message_id=read_message.message_id, user_id=user.id))
    db.session.commit()

    assert get_unread_message_count(user.id) == 2

    mark_all_unread_messages_as_read(user.id)

    assert get_unread_message_count(user.id) == 0
    assert MessageRead.query.filter_by(user_id=user.id).count() == 3


def test_message_service_serialize_group_message(app):
    user = _create_user("message-serialize@example.com", "message_serialize_user")
    message = Message(group_id=2, sender_id=user.id, content="serialize")
    db.session.add(message)
    db.session.commit()

    payload = serialize_group_message(message, "Sender")

    assert payload["message_id"] == message.message_id
    assert payload["sender_name"] == "Sender"
    assert payload["created_at"].endswith("Z")


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

    timeline = Timeline(user_id=owner.id, name="Task Role Timeline")
    db.session.add(timeline)
    db.session.commit()

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

    timeline = Timeline(user_id=owner.id, name="Fallback Timeline")
    db.session.add(timeline)
    db.session.commit()

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

    timeline = Timeline(user_id=owner.id, name="Manage Timeline")
    db.session.add(timeline)
    db.session.commit()

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

    timeline = Timeline(user_id=owner.id, name="Task Member Ops Timeline")
    db.session.add(timeline)
    db.session.flush()
    db.session.add(TimelineUser(timeline_id=timeline.id, user_id=owner.id, role=0))
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


def test_require_task_role_decorator(app, monkeypatch):
    @require_task_role("owner")
    def owner_only(task_id):
        return {"ok": True, "task_id": task_id}, 200

    with app.test_request_context("/"):
        monkeypatch.setattr("services.task_service.get_jwt_identity", lambda: "1")
        monkeypatch.setattr("services.task_service.get_user_task_role", lambda _uid, _tid: None)

        blocked = owner_only(task_id=1)
        assert blocked[1] == 403

        monkeypatch.setattr("services.task_service.get_user_task_role", lambda _uid, _tid: 1)
        blocked_owner = owner_only(task_id=1)
        assert blocked_owner[1] == 403

        monkeypatch.setattr("services.task_service.get_user_task_role", lambda _uid, _tid: 0)
        allowed = owner_only(task_id=1)
        assert allowed[1] == 200
        assert allowed[0]["ok"] is True


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


def test_timeline_service_find_unknown_fields_sorted():
    unknown = timeline_find_unknown_fields(
        {"name": "Timeline", "remark": "r", "x": 1},
        {"name", "remark"},
    )
    assert unknown == ["x"]


def test_generate_timeline_tasks_with_ai_missing_api_key(app, monkeypatch):
    owner = _create_user("timeline-ai-service-owner@example.com", "timeline_ai_service_owner")
    timeline = Timeline(user_id=owner.id, name="AI Service Timeline")
    db.session.add(timeline)
    db.session.commit()

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(TimelineAIGenerationError) as excinfo:
        generate_timeline_tasks_with_ai(
            timeline_id=timeline.id,
            project_name="AI Service Project",
            description="service layer prompt",
        )

    assert excinfo.value.code == "missing_api_key"


def test_generate_timeline_tasks_with_ai_success_and_json_decode_error(app, monkeypatch):
    owner = _create_user("timeline-ai-service-ok@example.com", "timeline_ai_service_ok")
    timeline = Timeline(user_id=owner.id, name="AI Service OK Timeline")
    db.session.add(timeline)
    db.session.flush()

    existing_task = Task(
        user_id=owner.id,
        timeline_id=timeline.id,
        name="existing service task",
        start_date=datetime(2026, 4, 1),
        end_date=datetime(2026, 4, 5),
    )
    db.session.add(existing_task)
    db.session.commit()

    # Mock successful LangChain generate_tasks response
    from unittest.mock import MagicMock
    mock_llm = MagicMock()
    mock_generate_tasks = MagicMock(return_value=[
        {"name": "service ai task", "priority": 1, "estimated_days": 2, "task_remark": "from chain"}
    ])

    # Patch both get_default_llm and generate_tasks at timeline_service module level
    monkeypatch.setattr("services.timeline_service.get_default_llm", MagicMock(return_value=mock_llm))
    monkeypatch.setattr("services.timeline_service.generate_tasks", mock_generate_tasks)

    payload = generate_timeline_tasks_with_ai(
        timeline_id=timeline.id,
        project_name="AI Service Project",
        description="service layer prompt",
    )

    assert payload["existingCount"] == 1
    assert payload["generatedCount"] == 1
    assert len(payload["tasks"]) == 2
    assert payload["tasks"][1]["name"] == "service ai task"
    assert payload["tasks"][1]["isExisting"] is False

    # Mock generate_tasks with ValueError (invalid JSON from LLM)
    mock_generate_tasks_error = MagicMock(side_effect=ValueError("Invalid JSON from LLM"))
    monkeypatch.setattr("services.timeline_service.generate_tasks", mock_generate_tasks_error)

    with pytest.raises(TimelineAIGenerationError) as excinfo:
        generate_timeline_tasks_with_ai(
            timeline_id=timeline.id,
            project_name="AI Service Project",
            description="service layer prompt",
        )

    assert excinfo.value.code == "generation_failed"


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
    assert task_payload["start_date"].endswith("Z")
    assert member_payload["email"] == owner.email


def test_require_timeline_role_decorator(app, monkeypatch):
    @require_timeline_role("owner")
    def owner_only(timeline_id):
        return {"ok": True, "timeline_id": timeline_id}, 200

    with app.test_request_context("/"):
        monkeypatch.setattr("services.timeline_service.get_jwt_identity", lambda: "1")
        monkeypatch.setattr("services.timeline_service.get_user_timeline_role", lambda _uid, _tid: None)

        blocked = owner_only(timeline_id=1)
        assert blocked[1] == 403

        monkeypatch.setattr("services.timeline_service.get_user_timeline_role", lambda _uid, _tid: 1)
        blocked_owner = owner_only(timeline_id=1)
        assert blocked_owner[1] == 403

        monkeypatch.setattr("services.timeline_service.get_user_timeline_role", lambda _uid, _tid: 0)
        allowed = owner_only(timeline_id=1)
        assert allowed[1] == 200
        assert allowed[0]["ok"] is True
