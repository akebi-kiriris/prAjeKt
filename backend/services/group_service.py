import random

from models import db
from models.group import Group
from models.group import GroupMember
from models.message import Message
from repositories.group_repository import (
    get_group_by_invite_code,
    get_group_member,
    list_group_members_query,
    list_group_messages_query,
    list_groups_for_user_query,
)


class GroupOperationError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def generate_unique_invite_code():
    while True:
        invite_code = f"{random.randint(0, 999999):06d}"
        existing = get_group_by_invite_code(invite_code)
        if not existing:
            return invite_code


def group_to_dict(group):
    return {
        'group_id': group.group_id,
        'group_name': group.group_name,
        'group_type': group.group_type,
        'invite_code': group.group_inviteCode,
        'created_at': group.created_at.isoformat() + 'Z' if group.created_at else None,
    }


def group_member_to_dict(member):
    return {
        'user_id': member.id,
        'name': member.name,
        'email': member.email,
    }


def group_message_to_dict(message):
    return {
        'message_id': message.message_id,
        'content': message.content,
        'sender_name': message.sender_name,
        'created_at': message.created_at.isoformat() + 'Z' if message.created_at else None,
    }


def is_group_member(group_id, user_id):
    return get_group_member(group_id, user_id) is not None


def group_room_name(group_id):
    return f'group_{group_id}'


def list_groups_for_user(user_id):
    groups = list_groups_for_user_query(user_id)
    return [group_to_dict(group) for group in groups]


def create_group_for_user(user_id, group_name):
    normalized_name = group_name.strip() if isinstance(group_name, str) else ''
    if not normalized_name:
        raise GroupOperationError('請輸入群組名稱', 400)

    invite_code = generate_unique_invite_code()
    new_group = Group(
        group_name=normalized_name,
        group_type='task',
        group_inviteCode=invite_code,
        created_by=user_id,
    )

    try:
        db.session.add(new_group)
        db.session.flush()
        db.session.add(GroupMember(group_id=new_group.group_id, user_id=user_id))
        db.session.commit()
        return {
            'group_id': new_group.group_id,
            'invite_code': invite_code,
        }
    except Exception as exc:
        db.session.rollback()
        raise GroupOperationError('建立群組失敗，請稍後再試', 500) from exc


def join_group_by_invite_code(user_id, invite_code):
    normalized_code = invite_code.strip() if isinstance(invite_code, str) else ''
    if not normalized_code:
        raise GroupOperationError('請輸入邀請碼', 400)

    group = get_group_by_invite_code(normalized_code)
    if not group:
        raise GroupOperationError('邀請碼無效', 404)

    existing = get_group_member(group.group_id, user_id)
    if existing:
        raise GroupOperationError('您已經是該群組成員', 409)

    try:
        db.session.add(GroupMember(group_id=group.group_id, user_id=user_id))
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise GroupOperationError('加入群組失敗，請稍後再試', 500) from exc


def leave_group_for_user(group_id, user_id):
    member = get_group_member(group_id, user_id)
    if not member:
        raise GroupOperationError('您不是該群組成員', 404)

    try:
        db.session.delete(member)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise GroupOperationError('離開群組失敗，請稍後再試', 500) from exc


def list_group_members_payload(group_id):
    members = list_group_members_query(group_id)
    return [group_member_to_dict(member) for member in members]


def list_group_messages_for_member(group_id, user_id):
    if not is_group_member(group_id, user_id):
        raise GroupOperationError('您不是該群組成員', 403)

    messages = list_group_messages_query(group_id)
    return [group_message_to_dict(message) for message in messages]


def send_group_message_for_member(group_id, user_id, content):
    normalized_content = content.strip() if isinstance(content, str) else ''
    if not normalized_content:
        raise GroupOperationError('訊息內容不可為空', 400)

    if not is_group_member(group_id, user_id):
        raise GroupOperationError('您不是該群組成員', 403)

    new_message = Message(
        group_id=group_id,
        sender_id=user_id,
        content=normalized_content,
    )

    try:
        db.session.add(new_message)
        db.session.commit()
        return new_message.message_id
    except Exception as exc:
        db.session.rollback()
        raise GroupOperationError('發送訊息失敗，請稍後再試', 500) from exc
