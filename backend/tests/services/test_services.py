from datetime import date, datetime, timezone

import pytest

from models import db
from models.group import Group, GroupMember
from models.message import Message, MessageRead
from models.notification import Notification
from models.task import Task
from models.task_comment import TaskComment
from models.task_user import TaskUser
from models.timeline import Timeline
from models.timeline_user import TimelineUser
from models.todo import Todo
from models.user import User
from services.auth_service import auth_user_to_dict, current_user_to_dict
from services.group_service import (
    generate_unique_invite_code,
    group_member_to_dict,
    group_message_to_dict,
    group_room_name,
    group_to_dict,
    is_group_member,
)
from services.message_service import (
    create_group_message,
    get_unread_messages_query,
    serialize_group_message,
)
from services.notification_service import notification_to_dict
from services.profile_service import (
    find_unknown_fields as profile_find_unknown_fields,
    profile_to_dict,
    search_user_to_dict,
)
from services.task_service import (
    build_task_member_list,
    can_manage_task_members,
    create_notification,
    find_unknown_fields as task_find_unknown_fields,
    get_user_task_role,
    require_task_role,
    task_comment_to_dict,
    task_list_item_to_dict,
    task_member_to_dict,
)
from services.timeline_service import (
    find_unknown_fields as timeline_find_unknown_fields,
    get_task_access,
    get_user_timeline_role,
    require_timeline_role,
    timeline_list_item_to_dict,
    timeline_member_item_to_dict,
    timeline_task_item_to_dict,
)
from services.todo_service import find_unknown_fields as todo_find_unknown_fields, todo_to_dict


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


def test_timeline_service_find_unknown_fields_sorted():
    unknown = timeline_find_unknown_fields(
        {"name": "Timeline", "remark": "r", "x": 1},
        {"name", "remark"},
    )
    assert unknown == ["x"]


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
