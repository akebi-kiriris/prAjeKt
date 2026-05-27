from datetime import datetime, timezone

import pytest

from models import db
from models.group import Group, GroupMember
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

def test_group_service_generate_unique_invite_code_skips_existing(app, monkeypatch, user_factory):
    owner = user_factory("group-owner@example.com", "group_owner")
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


def test_group_service_serializers_and_membership(app, user_factory):
    owner = user_factory("group-owner2@example.com", "group_owner2")
    member = user_factory("group-member2@example.com", "group_member2")

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
        type(
            "GroupMsg",
            (),
            {"message_id": 1, "content": "hi", "sender_name": "A", "created_at": datetime.now(timezone.utc)},
        )
    )

    assert group_payload["invite_code"] == "123456"
    assert group_payload["created_at"].endswith("Z")
    assert member_payload["email"] == member.email
    assert msg_payload["created_at"].endswith("Z")
    assert is_group_member(group.group_id, member.id) is True
    assert is_group_member(group.group_id, owner.id) is False
    assert group_room_name(group.group_id) == f"group_{group.group_id}"


def test_group_service_operations_and_errors(app, user_factory):
    owner = user_factory("group-service-owner@example.com", "group_service_owner")
    member = user_factory("group-service-member@example.com", "group_service_member")
    outsider = user_factory("group-service-outsider@example.com", "group_service_outsider")

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
    assert all("email" not in item for item in members)

    members_with_email = list_group_members_payload(group_id, include_email=True)
    assert all("email" in item for item in members_with_email)

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
