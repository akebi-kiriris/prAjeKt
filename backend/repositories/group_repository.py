from models import db
from models.group import Group, GroupMember
from models.group_ai_snapshot import GroupAISnapshot
from models.message import Message
from models.user import User
from datetime import datetime
from typing import TypedDict


class GroupMemberRow(TypedDict):
    user_id: int
    name: str
    email: str


class GroupMessageRow(TypedDict):
    message_id: int
    content: str
    created_at: datetime | None
    sender_name: str


def get_group_by_invite_code(invite_code: str) -> Group | None:
    return Group.query.filter_by(group_inviteCode=invite_code).first()


def get_group_member(group_id: int, user_id: int) -> GroupMember | None:
    return GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()


def list_groups_for_user_query(user_id: int) -> list[Group]:
    return (
        db.session.query(Group)
        .join(GroupMember, Group.group_id == GroupMember.group_id)
        .filter(GroupMember.user_id == user_id)
        .all()
    )


def list_group_members_query(group_id: int) -> list[GroupMemberRow]:
    rows = (
        db.session.query(User.id, User.name, User.email)
        .join(GroupMember, User.id == GroupMember.user_id)
        .filter(GroupMember.group_id == group_id)
        .all()
    )
    return [
        {
            "user_id": int(user_id),
            "name": str(name),
            "email": str(email),
        }
        for user_id, name, email in rows
    ]


def list_group_messages_query(group_id: int) -> list[GroupMessageRow]:
    rows = (
        db.session.query(
            Message.message_id,
            Message.content,
            Message.created_at,
            User.name.label('sender_name'),
        )
        .join(User, Message.sender_id == User.id)
        .filter(Message.group_id == group_id)
        .order_by(Message.created_at)
        .all()
    )
    return [
        {
            "message_id": int(message_id),
            "content": content or "",
            "created_at": created_at,
            "sender_name": str(sender_name),
        }
        for message_id, content, created_at, sender_name in rows
    ]


def count_group_messages_for_snapshot(group_id: int, cutoff: datetime) -> int:
    return (
        db.session.query(Message.message_id)
        .filter(Message.group_id == group_id)
        .filter(Message.created_at >= cutoff)
        .filter(Message.is_deleted.is_(False))
        .filter(Message.content.isnot(None))
        .count()
    )


def list_group_messages_for_snapshot(group_id: int, cutoff: datetime) -> list[GroupMessageRow]:
    rows = (
        db.session.query(
            Message.message_id,
            Message.content,
            Message.created_at,
            User.name.label('sender_name'),
        )
        .join(User, Message.sender_id == User.id)
        .filter(Message.group_id == group_id)
        .filter(Message.created_at >= cutoff)
        .filter(Message.is_deleted.is_(False))
        .filter(Message.content.isnot(None))
        .filter(Message.message_type != 'system')
        .order_by(Message.created_at.asc())
        .all()
    )
    return [
        {
            "message_id": int(message_id),
            "content": content or "",
            "created_at": created_at,
            "sender_name": str(sender_name),
        }
        for message_id, content, created_at, sender_name in rows
    ]


def get_latest_group_snapshot(group_id: int) -> GroupAISnapshot | None:
    return (
        GroupAISnapshot.query
        .filter_by(group_id=group_id)
        .order_by(GroupAISnapshot.created_at.desc())
        .first()
    )
