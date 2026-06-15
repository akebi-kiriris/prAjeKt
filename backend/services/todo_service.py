from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from models.todo import Todo
from repositories.session_repository import add_entity
from repositories.todo_repository import (
    get_active_todo_by_id_for_user,
    list_active_todos_for_user,
)
from contracts.todo_contracts import TodoCreateRequest, TodoUpdateRequest
from services.transactions import transaction

TODO_CREATE_ALLOWED_FIELDS = {'title', 'content', 'type', 'deadline', 'priority'}
TODO_UPDATE_ALLOWED_FIELDS = {'title', 'content', 'type', 'deadline', 'priority', 'completed'}


class TodoOperationError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def find_unknown_fields(payload: dict[str, Any], allowed_fields: set[str]) -> list[str]:
    """回傳 payload 中未預期的欄位鍵值。

    參數:
        payload: 輸入請求 payload。
        allowed_fields: 允許的欄位集合。

    回傳:
        排序後的未知欄位名稱。
    """
    return sorted(set(payload.keys()) - allowed_fields)


def todo_to_dict(todo: Todo) -> dict[str, Any]:
    """序列化待辦事項模型為 API payload。

    參數:
        todo: Todo 模型實例。

    回傳:
        可序列化的待辦事項 payload。
    """
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


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse_priority(priority: Any) -> int:
    try:
        parsed = int(priority)
    except (TypeError, ValueError):
        raise TodoOperationError('priority 必須是數字', 400)

    if parsed < 1 or parsed > 3:
        raise TodoOperationError('priority 必須介於 1 到 3', 400)

    return parsed


def _parse_deadline(deadline_value: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(deadline_value) if deadline_value else None
    except ValueError:
        raise TodoOperationError('deadline 格式錯誤', 400)


def _find_active_todo_or_404(todo_id: int, user_id: int) -> Todo:
    todo = get_active_todo_by_id_for_user(todo_id, user_id)
    if not todo:
        raise TodoOperationError('找不到該待辦事項', 404)
    return todo


def list_todos_for_user(user_id: int, todo_id: int | None = None) -> list[Todo]:
    """列出使用者待辦事項，或回傳指定待辦事項。

    參數:
        user_id: 擁有者使用者 id。
        todo_id: 可選的單一待辦事項 id。

    回傳:
        Todo 模型清單。

    例外:
        TodoOperationError: 指定待辦事項不存在。
    """
    if todo_id:
        todo = _find_active_todo_or_404(todo_id, user_id)
        return [todo]

    return list_active_todos_for_user(user_id)


def create_todo_for_user(user_id: int, data: dict[str, Any]) -> int:
    """為使用者建立待辦事項。

    參數:
        user_id: 擁有者使用者 id。
        data: 建立 payload。

    回傳:
        新建立的待辦事項 id。

    例外:
        TodoOperationError: 驗證失敗或資料寫入失敗。
    """
    unknown_fields = find_unknown_fields(data, TODO_CREATE_ALLOWED_FIELDS)
    if unknown_fields:
        raise TodoOperationError(f'不允許的欄位: {", ".join(unknown_fields)}', 400)
    try:
        validated = TodoCreateRequest.model_validate(data)
        data = validated.model_dump(exclude_unset=True)
    except ValidationError as err:
        first_error = err.errors()[0] if err.errors() else {}
        raise TodoOperationError(str(first_error.get("msg") or "參數格式錯誤"), 400) from err

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

    with transaction(TodoOperationError, '待辦事項新增失敗，請稍後再試'):
        add_entity(new_todo)

    return new_todo.id


def update_todo_for_user(todo_id: int, user_id: int, data: dict[str, Any]) -> None:
    """更新使用者的單一待辦事項。

    參數:
        todo_id: 目標待辦事項 id。
        user_id: 擁有者使用者 id。
        data: 更新 payload。

    例外:
        TodoOperationError: 驗證失敗或交易失敗。
    """
    todo = _find_active_todo_or_404(todo_id, user_id)

    unknown_fields = find_unknown_fields(data, TODO_UPDATE_ALLOWED_FIELDS)
    if unknown_fields:
        raise TodoOperationError(f'不允許的欄位: {", ".join(unknown_fields)}', 400)
    try:
        validated = TodoUpdateRequest.model_validate(data)
        data = validated.model_dump(exclude_unset=True)
    except ValidationError as err:
        first_error = err.errors()[0] if err.errors() else {}
        raise TodoOperationError(str(first_error.get("msg") or "參數格式錯誤"), 400) from err

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

    with transaction(TodoOperationError, '待辦事項更新失敗，請稍後再試'):
        pass


def soft_delete_todo_for_user(todo_id: int, user_id: int) -> None:
    """軟刪除單一待辦事項。

    參數:
        todo_id: 目標待辦事項 id。
        user_id: 擁有者使用者 id。

    例外:
        TodoOperationError: 待辦事項不存在或刪除交易失敗。
    """
    todo = _find_active_todo_or_404(todo_id, user_id)

    with transaction(TodoOperationError, '待辦事項刪除失敗，請稍後再試'):
        todo.deleted_at = _utcnow_naive()


def toggle_todo_for_user(todo_id: int, user_id: int) -> bool:
    """切換待辦事項完成狀態。

    參數:
        todo_id: 目標待辦事項 id。
        user_id: 擁有者使用者 id。

    回傳:
        更新後的完成狀態。

    例外:
        TodoOperationError: 待辦事項不存在或更新交易失敗。
    """
    todo = _find_active_todo_or_404(todo_id, user_id)
    todo.completed = not todo.completed
    todo.completed_at = _utcnow_naive() if todo.completed else None

    with transaction(TodoOperationError, '狀態更新失敗，請稍後再試'):
        pass

    return todo.completed

