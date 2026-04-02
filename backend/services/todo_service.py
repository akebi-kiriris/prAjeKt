from datetime import datetime, timezone

from models import db
from models.todo import Todo

TODO_CREATE_ALLOWED_FIELDS = {'title', 'content', 'type', 'deadline', 'priority'}
TODO_UPDATE_ALLOWED_FIELDS = {'title', 'content', 'type', 'deadline', 'priority', 'completed'}


class TodoOperationError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def find_unknown_fields(payload, allowed_fields):
    return sorted(set(payload.keys()) - allowed_fields)


def todo_to_dict(todo: Todo):
    return {
        'id': todo.id,
        'title': todo.title,
        'content': todo.content,
        'type': todo.type,
        'deadline': todo.deadline.isoformat() + 'Z' if todo.deadline else None,
        'completed': todo.completed,
        'priority': todo.priority,
        'created_at': todo.created_at.isoformat() + 'Z' if todo.created_at else None,
        'updated_at': todo.updated_at.isoformat() + 'Z' if todo.updated_at else None,
    }


def _utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse_priority(priority):
    try:
        parsed = int(priority)
    except (TypeError, ValueError):
        raise TodoOperationError('priority 必須是數字', 400)

    if parsed < 1 or parsed > 3:
        raise TodoOperationError('priority 必須介於 1 到 3', 400)

    return parsed


def _parse_deadline(deadline_value):
    try:
        return datetime.fromisoformat(deadline_value) if deadline_value else None
    except ValueError:
        raise TodoOperationError('deadline 格式錯誤', 400)


def _find_active_todo_or_404(todo_id, user_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).filter(Todo.deleted_at.is_(None)).first()
    if not todo:
        raise TodoOperationError('找不到該待辦事項', 404)
    return todo


def list_todos_for_user(user_id, todo_id=None):
    if todo_id:
        todo = _find_active_todo_or_404(todo_id, user_id)
        return [todo]

    return (
        Todo.query
        .filter_by(user_id=user_id)
        .filter(Todo.deleted_at.is_(None))
        .order_by(Todo.completed, Todo.deadline)
        .all()
    )


def create_todo_for_user(user_id, data):
    unknown_fields = find_unknown_fields(data, TODO_CREATE_ALLOWED_FIELDS)
    if unknown_fields:
        raise TodoOperationError(f'不允許的欄位: {", ".join(unknown_fields)}', 400)

    content = data.get('content')
    title = data.get('title')
    if not isinstance(content, str):
        raise TodoOperationError('內容必須是字串', 400)
    if not content or not title:
        raise TodoOperationError('請確認是否有填入事項名稱或內容', 400)

    priority = _parse_priority(data.get('priority', 2))
    deadline = _parse_deadline(data.get('deadline'))

    new_todo = Todo(
        user_id=user_id,
        title=data['title'],
        content=data['content'],
        type=data.get('type'),
        deadline=deadline,
        completed=False,
        priority=priority,
    )

    try:
        db.session.add(new_todo)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise TodoOperationError('待辦事項新增失敗，請稍後再試', 500) from exc

    return new_todo.id


def update_todo_for_user(todo_id, user_id, data):
    todo = _find_active_todo_or_404(todo_id, user_id)

    unknown_fields = find_unknown_fields(data, TODO_UPDATE_ALLOWED_FIELDS)
    if unknown_fields:
        raise TodoOperationError(f'不允許的欄位: {", ".join(unknown_fields)}', 400)

    if 'title' in data:
        if not isinstance(data['title'], str) or not data['title'].strip():
            raise TodoOperationError('事項名稱必須是非空字串', 400)
        todo.title = data['title'].strip()

    if 'content' in data:
        if not isinstance(data['content'], str):
            raise TodoOperationError('內容必須是字串', 400)
        todo.content = data['content']

    if 'type' in data:
        if data['type'] is not None and not isinstance(data['type'], str):
            raise TodoOperationError('type 必須是字串或 null', 400)
        todo.type = data['type']

    if 'deadline' in data:
        todo.deadline = _parse_deadline(data['deadline'])

    if 'priority' in data:
        todo.priority = _parse_priority(data['priority'])

    if 'completed' in data:
        if not isinstance(data['completed'], bool):
            raise TodoOperationError('completed 必須是布林值', 400)
        todo.completed = data['completed']
        todo.completed_at = _utcnow_naive() if data['completed'] else None

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise TodoOperationError('待辦事項更新失敗，請稍後再試', 500) from exc


def soft_delete_todo_for_user(todo_id, user_id):
    todo = _find_active_todo_or_404(todo_id, user_id)

    try:
        todo.deleted_at = _utcnow_naive()
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise TodoOperationError('待辦事項刪除失敗，請稍後再試', 500) from exc


def toggle_todo_for_user(todo_id, user_id):
    todo = _find_active_todo_or_404(todo_id, user_id)
    todo.completed = not todo.completed
    todo.completed_at = _utcnow_naive() if todo.completed else None

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise TodoOperationError('狀態更新失敗，請稍後再試', 500) from exc

    return todo.completed
