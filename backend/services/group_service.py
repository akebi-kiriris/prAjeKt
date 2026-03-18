import random

from models.group import Group
from models.group import GroupMember


def generate_unique_invite_code():
    while True:
        invite_code = f"{random.randint(0, 999999):06d}"
        existing = Group.query.filter_by(group_inviteCode=invite_code).first()
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
    return GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first() is not None


def group_room_name(group_id):
    return f'group_{group_id}'
