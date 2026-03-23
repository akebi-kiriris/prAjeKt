from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from models import db
from models.notification import Notification
from models.task import Task
from models.task_user import TaskUser
from models.timeline_user import TimelineUser
from models.user import User

TASK_CREATE_ALLOWED_FIELDS = {
    'name',
    'timeline_id',
    'priority',
    'status',
    'tags',
    'estimated_hours',
    'start_date',
    'end_date',
    'task_remark',
    'isWork',
}

TASK_UPDATE_ALLOWED_FIELDS = {
    'name',
    'timeline_id',
    'priority',
    'status',
    'tags',
    'estimated_hours',
    'actual_hours',
    'start_date',
    'end_date',
    'task_remark',
    'isWork',
}

TASK_STATUS_VALUES = {'pending', 'in_progress', 'review', 'completed', 'cancelled'}


def find_unknown_fields(payload, allowed_fields):
    return sorted(set(payload.keys()) - allowed_fields)


def create_notification(user_id, ntype, title, content=None, link=None):
    """建立通知的工具函式，失敗時靜默不影響主流程。"""
    try:
        notif = Notification(
            user_id=user_id,
            type=ntype,
            title=title,
            content=content,
            link=link,
        )
        db.session.add(notif)
    except Exception:
        pass


def get_user_task_role(user_id, task_id):
    """查詢使用者在某任務的角色。"""
    member = TaskUser.query.filter_by(task_id=task_id, user_id=user_id).first()
    if member:
        return member.role

    task = Task.query.filter_by(task_id=task_id).first()
    if task and task.timeline_id:
        tl_member = TimelineUser.query.filter_by(
            timeline_id=task.timeline_id,
            user_id=user_id,
        ).first()
        if tl_member is not None:
            return tl_member.role

    return None


def can_manage_task_members(operator_user_id, task):
    """檢查是否可管理任務成員（任務主責/建立者/專案主責）。"""
    task_role = get_user_task_role(operator_user_id, task.task_id)
    is_task_owner = (task_role == 0) or (task.user_id == operator_user_id)

    is_timeline_owner = False
    if task.timeline_id:
        tl_role = TimelineUser.query.filter_by(
            timeline_id=task.timeline_id,
            user_id=operator_user_id,
        ).first()
        is_timeline_owner = tl_role is not None and tl_role.role == 0

    return is_task_owner or is_timeline_owner


def require_task_role(required_role='member'):
    """Decorator：檢查當前使用者在任務中的角色。"""

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_id = int(get_jwt_identity())
            task_id = kwargs.get('task_id')
            role = get_user_task_role(user_id, task_id)
            if role is None:
                return jsonify({'error': '你不是此任務成員'}), 403
            if required_role == 'owner' and role != 0:
                return jsonify({'error': '只有負責人可執行此操作'}), 403
            return f(*args, **kwargs)

        return wrapper

    return decorator


def task_member_to_dict(task_member, user, include_contact=False):
    payload = {
        'user_id': user.id,
        'name': user.name,
        'role': task_member.role,
    }

    if include_contact:
        payload['email'] = user.email
        payload['avatar'] = user.avatar
        payload['assigned_at'] = task_member.assigned_at.isoformat() + 'Z' if task_member.assigned_at else None

    return payload


def build_task_member_list(task_id, viewer_user_id=None, include_contact=False):
    members = TaskUser.query.filter_by(task_id=task_id).all()
    result = []
    viewer_role = None

    for member in members:
        if viewer_user_id is not None and member.user_id == viewer_user_id:
            viewer_role = member.role

        user = User.query.get(member.user_id)
        if user:
            result.append(task_member_to_dict(member, user, include_contact=include_contact))

    return result, viewer_role


def build_task_member_list_from_map(task_id, task_users_map, users_map, viewer_user_id=None, include_contact=False):
    """N+1 回避版：從預先批次載入的映射中建立任務成員清單。

    Args:
        task_id: 目標任務 ID。
        task_users_map: dict[task_id -> list[TaskUser]]，由呼叫端批次查詢後傳入。
        users_map: dict[user_id -> User]，由呼叫端批次查詢後傳入。
        viewer_user_id: 當前檢視者的 user_id（用於判斷其角色）。
        include_contact: 是否包含聯絡資訊欄位。

    Returns:
        (member_list, viewer_role) — 與 build_task_member_list 相同的回傳格式。
    """
    members = task_users_map.get(task_id, [])
    result = []
    viewer_role = None

    for member in members:
        if viewer_user_id is not None and member.user_id == viewer_user_id:
            viewer_role = member.role

        user = users_map.get(member.user_id)
        if user:
            result.append(task_member_to_dict(member, user, include_contact=include_contact))

    return result, viewer_role


def task_list_item_to_dict(task, member_list, subtask_list, is_owner):
    return {
        'task_id': task.task_id,
        'name': task.name,
        'completed': task.completed,
        'timeline_id': task.timeline_id,
        'priority': task.priority,
        'status': task.status,
        'tags': task.tags,
        'estimated_hours': task.estimated_hours,
        'actual_hours': task.actual_hours,
        'members': member_list,
        'subtasks': subtask_list,
        'created_at': task.created_at.isoformat() + 'Z' if task.created_at else None,
        'start_date': task.start_date.isoformat() + 'Z' if task.start_date else None,
        'end_date': task.end_date.isoformat() + 'Z' if task.end_date else None,
        'updated_at': task.updated_at.isoformat() + 'Z' if task.updated_at else None,
        'task_remark': task.task_remark,
        'isWork': task.isWork,
        'is_owner': is_owner,
    }


def task_comment_to_dict(comment, user):
    return {
        'comment_id': comment.comment_id,
        'user_id': comment.user_id,
        'user_name': user.name if user else '未知使用者',
        'user_avatar': user.avatar if user else None,
        'task_message': comment.task_message,
        'created_at': comment.created_at.isoformat() + 'Z' if comment.created_at else None,
    }
