from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from services.task_service import get_user_task_role
from services.timeline_service import get_user_timeline_role


def require_task_role(required_role='member'):
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


def require_timeline_role(required_role='member'):
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
