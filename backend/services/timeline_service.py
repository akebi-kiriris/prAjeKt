from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from models.task_user import TaskUser
from models.timeline_user import TimelineUser

TIMELINE_UPDATE_ALLOWED_FIELDS = {'name', 'start_date', 'end_date', 'remark'}


def find_unknown_fields(payload, allowed_fields):
    return sorted(set(payload.keys()) - allowed_fields)


def get_user_timeline_role(user_id, timeline_id):
    """查詢使用者在某專案的角色。"""
    member = TimelineUser.query.filter_by(timeline_id=timeline_id, user_id=user_id).first()
    return member.role if member is not None else None


def get_task_access(user_id, task):
    """查詢使用者對某任務的存取權限（支援 timeline 任務與獨立任務）。"""
    if task.timeline_id:
        role = get_user_timeline_role(user_id, task.timeline_id)
        if role is not None:
            return role

    member = TaskUser.query.filter_by(task_id=task.task_id, user_id=user_id).first()
    if member:
        return member.role

    if task.user_id == user_id:
        return 0

    return None


def require_timeline_role(required_role='member'):
    """Decorator：檢查當前使用者在專案中的角色。"""

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_id = int(get_jwt_identity())
            timeline_id = kwargs.get('timeline_id')
            role = get_user_timeline_role(user_id, timeline_id)
            if role is None:
                return jsonify({'error': '你不是此專案成員'}), 403
            if required_role == 'owner' and role != 0:
                return jsonify({'error': '只有負責人可執行此操作'}), 403
            return f(*args, **kwargs)

        return wrapper

    return decorator


def timeline_list_item_to_dict(timeline, role, total_tasks, completed_tasks):
    return {
        'id': timeline.id,
        'name': timeline.name,
        'startDate': timeline.start_date.isoformat() + 'Z' if timeline.start_date else None,
        'endDate': timeline.end_date.isoformat() + 'Z' if timeline.end_date else None,
        'remark': timeline.remark,
        'role': role,
        'totalTasks': total_tasks,
        'completedTasks': completed_tasks,
    }


def timeline_task_item_to_dict(task, assignee_name, assistant_list):
    return {
        'task_id': task.task_id,
        'name': task.name,
        'assignee': assignee_name,
        'assistant': assistant_list,
        'start_date': task.start_date.isoformat() + 'Z' if task.start_date else None,
        'end_date': task.end_date.isoformat() + 'Z' if task.end_date else None,
        'completed': task.completed,
        'timeline_id': task.timeline_id,
        'remark': task.task_remark,
        'isWork': task.isWork,
        'priority': task.priority,
        'status': task.status,
        'tags': task.tags,
    }


def timeline_member_item_to_dict(timeline_member, user):
    return {
        'user_id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email,
        'role': timeline_member.role,
    }
