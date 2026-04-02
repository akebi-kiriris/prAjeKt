from models import db
from models.group import Group, GroupMember
from models.message import Message
from models.user import User


def get_group_by_invite_code(invite_code):
    return Group.query.filter_by(group_inviteCode=invite_code).first()


def get_group_member(group_id, user_id):
    return GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()


def list_groups_for_user_query(user_id):
    return (
        db.session.query(Group)
        .join(GroupMember, Group.group_id == GroupMember.group_id)
        .filter(GroupMember.user_id == user_id)
        .all()
    )


def list_group_members_query(group_id):
    return (
        db.session.query(User.id, User.name, User.email)
        .join(GroupMember, User.id == GroupMember.user_id)
        .filter(GroupMember.group_id == group_id)
        .all()
    )


def list_group_messages_query(group_id):
    return (
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
