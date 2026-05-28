from collections import defaultdict
from datetime import datetime, timedelta, timezone
import json
import os
import re
import time
import uuid
from collections.abc import Iterable
from typing import Any

from pydantic import ValidationError
from models.subtask import Subtask
from models.task import Task
from models.task_comment import TaskComment
from models.task_user import TaskUser
from models.timeline import TaskFile
from werkzeug.utils import secure_filename
from services.ai_provider import get_ai_provider
from services.transactions import transaction
from repositories.task_repository import (
    build_notification_entity,
    build_task_entity,
    build_task_member_entity,
    demote_task_members_to_collaborator,
    get_active_task_by_id,
    get_active_task_comment,
    get_active_task_ids_for_timeline,
    get_max_subtask_sort_order,
    get_active_tasks_by_ids,
    get_assigned_task_ids_for_user,
    get_subtask,
    get_task_by_id,
    get_task_file,
    get_task_file_by_filename,
    get_task_member,
    get_user_by_id,
    get_users_by_ids,
    get_owned_active_tasks,
    get_timeline_member,
    get_timeline_ids_for_user,
    get_timeline_membership_role,
    get_upcoming_candidate_tasks_for_user,
    list_active_task_comments,
    list_subtasks,
    list_subtasks_by_task_ids,
    list_task_files,
    list_task_members,
    list_task_members_by_task_ids,
    list_timeline_members,
    remove_task_member,
)
from repositories.session_repository import add_entity, delete_entity, flush_session
from services.contracts.task_contracts import TaskCreateInput, TaskStatusUpdateInput, TaskUpdateInput

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
    'assignee_user_ids',
    'depends_on_task_ids',
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
    'depends_on_task_ids',
}

TASK_STATUS_VALUES = {'pending', 'in_progress', 'review', 'completed', 'cancelled'}
ALLOWED_TASK_FILE_EXTENSIONS = {
    'txt',
    'pdf',
    'png',
    'jpg',
    'jpeg',
    'gif',
    'webp',
    'doc',
    'docx',
    'xls',
    'xlsx',
    'ppt',
    'pptx',
    'zip',
    'csv',
    'mp4',
    'mov',
}
MAX_TASK_FILE_SIZE = 10 * 1024 * 1024


class TaskOperationError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def find_unknown_fields(payload: dict[str, Any], allowed_fields: set[str]) -> list[str]:
    return sorted(set(payload.keys()) - allowed_fields)


def normalize_assignee_user_ids(raw_value: Any) -> list[int]:
    if raw_value in (None, ''):
        return []

    if not isinstance(raw_value, list):
        raise TaskOperationError('assignee_user_ids 必須是陣列', 400)

    normalized = []
    seen = set()
    for item in raw_value:
        try:
            user_id = int(item)
        except (TypeError, ValueError):
            raise TaskOperationError('assignee_user_ids 只允許整數 ID', 400)

        if user_id <= 0:
            raise TaskOperationError('assignee_user_ids 只允許正整數 ID', 400)

        if user_id in seen:
            continue

        seen.add(user_id)
        normalized.append(user_id)

    return normalized


def normalize_depends_on_task_ids(raw_value: Any) -> list[int]:
    if raw_value in (None, ''):
        return []

    if not isinstance(raw_value, list):
        raise TaskOperationError('depends_on_task_ids 必須是陣列', 400)

    normalized = []
    seen = set()
    for item in raw_value:
        try:
            task_id = int(item)
        except (TypeError, ValueError):
            raise TaskOperationError('depends_on_task_ids 只允許整數 ID', 400)

        if task_id <= 0:
            raise TaskOperationError('depends_on_task_ids 只允許正整數 ID', 400)

        if task_id in seen:
            continue

        seen.add(task_id)
        normalized.append(task_id)

    return normalized


def validate_dependency_task_ids(
    timeline_id: int | None,
    depends_on_task_ids: list[int],
    current_task_id: int | None = None,
) -> None:
    if not depends_on_task_ids:
        return

    if timeline_id in (None, ''):
        raise TaskOperationError('設定 depends_on_task_ids 前需先指定 timeline_id', 400)

    if current_task_id is not None and current_task_id in depends_on_task_ids:
        raise TaskOperationError('depends_on_task_ids 不可包含自己', 400)

    active_task_ids = set(get_active_task_ids_for_timeline(timeline_id))

    invalid_ids = sorted(task_id for task_id in depends_on_task_ids if task_id not in active_task_ids)
    if invalid_ids:
        raise TaskOperationError('depends_on_task_ids 包含非同專案任務', 400)


def _build_task_create_payload(data: dict[str, Any]) -> dict[str, Any]:
    create_input = _validate_task_create_input(data)

    return {
        'status': create_input.status,
        'priority': create_input.priority,
        'start_date': create_input.start_date,
        'end_date': create_input.end_date,
        'assignee_user_ids': normalize_assignee_user_ids(data.get('assignee_user_ids')),
        'depends_on_task_ids': normalize_depends_on_task_ids(data.get('depends_on_task_ids')),
        'timeline_id': create_input.timeline_id,
    }


def _validation_error_to_task_operation_error(err: ValidationError) -> TaskOperationError:
    first_error = err.errors()[0] if err.errors() else {}
    message = str(first_error.get('msg') or '參數格式錯誤')
    return TaskOperationError(message, 400)


def _validate_task_create_input(data: dict[str, Any]) -> TaskCreateInput:
    payload = {
        'status': data.get('status', 'pending'),
        'priority': data.get('priority', 2),
        'start_date': data.get('start_date'),
        'end_date': data.get('end_date'),
        'timeline_id': data.get('timeline_id'),
    }
    try:
        return TaskCreateInput.model_validate(payload)
    except ValidationError as err:
        raise _validation_error_to_task_operation_error(err) from err


def _validate_task_update_input(data: dict[str, Any]) -> TaskUpdateInput:
    try:
        return TaskUpdateInput.model_validate(data)
    except ValidationError as err:
        raise _validation_error_to_task_operation_error(err) from err


def _validate_task_status_update_input(new_status: str) -> TaskStatusUpdateInput:
    try:
        return TaskStatusUpdateInput(status=new_status)
    except ValidationError as err:
        raise _validation_error_to_task_operation_error(err) from err


def _validate_task_create_membership(timeline_id: int | None, assignee_user_ids: list[int]) -> None:
    if not timeline_id or not assignee_user_ids:
        return

    timeline_member_ids = {member.user_id for member in list_timeline_members(timeline_id)}
    invalid_assignees = [member_id for member_id in assignee_user_ids if member_id not in timeline_member_ids]
    if invalid_assignees:
        raise TaskOperationError('指派名單包含非專案成員', 400)


def _create_task_with_members_and_notifications(
    user_id: int,
    data: dict[str, Any],
    payload: dict[str, Any],
) -> int:
    with transaction(TaskOperationError, '任務新增失敗，請稍後再試'):
        new_task = build_task_entity(
            user_id=user_id,
            name=data['name'],
            timeline_id=payload['timeline_id'],
            priority=payload['priority'],
            status=payload['status'],
            tags=data.get('tags'),
            estimated_hours=data.get('estimated_hours'),
            start_date=payload['start_date'],
            end_date=payload['end_date'],
            task_remark=data.get('task_remark'),
            is_work=data.get('isWork', 0),
            depends_on_task_ids=payload['depends_on_task_ids'],
        )
        new_task.change_status(payload['status'], completed_at_fallback=_utcnow_naive())

        add_entity(new_task)
        flush_session()

        add_entity(build_task_member_entity(task_id=new_task.task_id, user_id=user_id, role=0))

        actor = get_user_by_id(user_id)
        actor_name = actor.name if actor else '某人'

        for member_id in payload['assignee_user_ids']:
            if member_id == user_id:
                continue

            add_entity(build_task_member_entity(task_id=new_task.task_id, user_id=member_id, role=1))
            create_notification(
                user_id=member_id,
                ntype='task_assigned',
                title=f'你被指派到任務「{new_task.name}」',
                content=f'{actor_name} 在建立任務時將你加入「{new_task.name}」',
                link='/tasks',
            )

        return new_task.task_id


def create_notification(
    user_id: int,
    ntype: str,
    title: str,
    content: str | None = None,
    link: str | None = None,
) -> None:
    """建立通知的工具函式，失敗時靜默不影響主流程。"""
    try:
        notif = build_notification_entity(
            user_id=user_id,
            ntype=ntype,
            title=title,
            content=content,
            link=link,
        )
        add_entity(notif)
    except Exception:
        pass


def get_user_task_role(user_id: int, task_id: int) -> int | None:
    """查詢使用者在某任務的角色。"""
    member = get_task_member(task_id, user_id)
    if member:
        return member.role

    task = get_task_by_id(task_id)
    if task and task.timeline_id:
        tl_member = get_timeline_member(task.timeline_id, user_id)
        if tl_member is not None:
            return tl_member.role

    return None


def can_manage_task_members(operator_user_id: int, task: Task) -> bool:
    """檢查是否可管理任務成員（任務主責/建立者/專案主責）。"""
    task_role = get_user_task_role(operator_user_id, task.task_id)
    is_task_owner = (task_role == 0) or (task.user_id == operator_user_id)

    is_timeline_owner = False
    if task.timeline_id:
        tl_role = get_timeline_member(task.timeline_id, operator_user_id)
        is_timeline_owner = tl_role is not None and tl_role.role == 0

    return is_task_owner or is_timeline_owner


def task_member_to_dict(task_member: TaskUser, user: Any, include_contact: bool = False) -> dict[str, Any]:
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


def build_task_member_list(
    task_id: int,
    viewer_user_id: int | None = None,
    include_contact: bool = False,
    users_map: dict[int, Any] | None = None,
) -> list[dict[str, Any]]:
    members = list_task_members(task_id)
    result = []
    viewer_role = None

    if users_map is None:
        users_map = {
            user.id: user
            for user in get_users_by_ids([member.user_id for member in members])
        }

    for member in members:
        if viewer_user_id is not None and member.user_id == viewer_user_id:
            viewer_role = member.role

        user = users_map.get(member.user_id)
        if user:
            result.append(task_member_to_dict(member, user, include_contact=include_contact))

    return result, viewer_role


def task_list_item_to_dict(
    task: Task,
    member_list: list[dict[str, Any]],
    subtask_list: list[dict[str, Any]],
    is_owner: bool,
) -> dict[str, Any]:
    return {
        'task_id': task.task_id,
        'name': task.name,
        'completed': task.completed,
        'completed_at': task.completed_at.isoformat() + 'Z' if task.completed_at else None,
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
        'depends_on_task_ids': task.depends_on_task_ids or [],
        'is_owner': is_owner,
    }


def task_comment_to_dict(comment: TaskComment, user: Any) -> dict[str, Any]:
    return {
        'comment_id': comment.comment_id,
        'user_id': comment.user_id,
        'user_name': user.name if user else '未知使用者',
        'user_avatar': user.avatar if user else None,
        'task_message': comment.task_message,
        'created_at': comment.created_at.isoformat() + 'Z' if comment.created_at else None,
    }


def _utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _find_active_task_or_404(task_id):
    task = get_active_task_by_id(task_id)
    if not task:
        raise TaskOperationError('找不到該任務', 404)
    return task


def list_tasks_for_user(user_id: int) -> list[dict[str, Any]]:
    own_tasks = get_owned_active_tasks(user_id)
    assigned_task_ids = get_assigned_task_ids_for_user(user_id)
    assigned_tasks = get_active_tasks_by_ids(assigned_task_ids)

    all_tasks = {task.task_id: task for task in own_tasks + assigned_tasks}
    tasks = sorted(all_tasks.values(), key=lambda task: (task.completed, task.end_date or datetime.max))

    task_ids = [task.task_id for task in tasks]
    members_by_task = defaultdict(list)
    member_rows = list_task_members_by_task_ids(task_ids)
    user_ids = set()
    for member in member_rows:
        members_by_task[member.task_id].append(member)
        user_ids.add(member.user_id)

    users_map = {user.id: user for user in get_users_by_ids(user_ids)}

    subtasks_by_task = defaultdict(list)
    for subtask in list_subtasks_by_task_ids(task_ids):
        subtasks_by_task[subtask.task_id].append(subtask)

    result = []
    for task in tasks:
        member_list = []
        current_user_role = None

        for member in members_by_task.get(task.task_id, []):
            if current_user_role is None and member.user_id == user_id:
                current_user_role = member.role

            user = users_map.get(member.user_id)
            if user:
                member_list.append(task_member_to_dict(member, user))

        if current_user_role is None and task.timeline_id:
            current_user_role = get_timeline_membership_role(task.timeline_id, user_id)

        is_owner = (current_user_role == 0) or (task.user_id == user_id)

        subtask_list = [subtask.to_dict() for subtask in subtasks_by_task.get(task.task_id, [])]

        result.append(task_list_item_to_dict(task, member_list, subtask_list, is_owner))

    return result


def create_task_for_user(user_id: int, data: dict[str, Any]) -> int:
    unknown_fields = find_unknown_fields(data, TASK_CREATE_ALLOWED_FIELDS)
    if unknown_fields:
        raise TaskOperationError(f'不允許的欄位: {", ".join(unknown_fields)}', 400)

    if not data.get('name') or not data.get('end_date'):
        raise TaskOperationError('請提供標題和截止日期', 400)

    payload = _build_task_create_payload(data)
    _validate_task_create_membership(
        timeline_id=payload['timeline_id'],
        assignee_user_ids=payload['assignee_user_ids'],
    )
    validate_dependency_task_ids(payload['timeline_id'], payload['depends_on_task_ids'])
    return _create_task_with_members_and_notifications(user_id=user_id, data=data, payload=payload)


def update_task_for_member(task_id: int, data: dict[str, Any]) -> None:
    task = _find_active_task_or_404(task_id)

    unknown_fields = find_unknown_fields(data, TASK_UPDATE_ALLOWED_FIELDS)
    if unknown_fields:
        raise TaskOperationError(f'不允許的欄位: {", ".join(unknown_fields)}', 400)
    update_input = _validate_task_update_input(data)

    with transaction(TaskOperationError, '任務更新失敗，請稍後再試'):
        if 'priority' in data:
            task.priority = update_input.priority

        if 'name' in data:
            task.name = update_input.name

        target_timeline_id = task.timeline_id
        if 'timeline_id' in data:
            target_timeline_id = data['timeline_id']
            task.timeline_id = target_timeline_id

        if 'depends_on_task_ids' in data:
            depends_on_task_ids = normalize_depends_on_task_ids(data.get('depends_on_task_ids'))
            validate_dependency_task_ids(
                target_timeline_id,
                depends_on_task_ids,
                current_task_id=task.task_id,
            )
            task.depends_on_task_ids = depends_on_task_ids
        elif 'timeline_id' in data:
            if target_timeline_id in (None, ''):
                task.depends_on_task_ids = []
            else:
                validate_dependency_task_ids(
                    target_timeline_id,
                    task.depends_on_task_ids or [],
                    current_task_id=task.task_id,
                )

        if 'status' in data:
            next_status = update_input.status
            task.change_status(next_status, completed_at_fallback=_utcnow_naive())

        if 'tags' in data:
            task.tags = data['tags']

        if 'estimated_hours' in data:
            task.estimated_hours = data['estimated_hours']

        if 'actual_hours' in data:
            task.actual_hours = data['actual_hours']

        if 'task_remark' in data:
            task.task_remark = data['task_remark']

        if 'isWork' in data:
            task.isWork = data['isWork']

        if 'start_date' in data:
            task.start_date = update_input.start_date

        if 'end_date' in data:
            task.end_date = update_input.end_date


def soft_delete_task_for_owner(task_id: int) -> None:
    task = _find_active_task_or_404(task_id)
    with transaction(TaskOperationError, '任務刪除失敗，請稍後再試'):
        task.deleted_at = _utcnow_naive()


def toggle_task_for_member(task_id: int) -> bool:
    task = _find_active_task_or_404(task_id)
    with transaction(TaskOperationError, '狀態更新失敗，請稍後再試'):
        task.change_status('pending' if task.completed else 'completed', completed_at_fallback=_utcnow_naive())
    return task.completed


def list_upcoming_tasks_for_user(user_id: int) -> list[dict[str, Any]]:
    today = datetime.now(timezone.utc).date()
    threshold = today + timedelta(days=3)

    assigned_task_ids = get_assigned_task_ids_for_user(user_id)
    timeline_ids = get_timeline_ids_for_user(user_id)
    tasks = get_upcoming_candidate_tasks_for_user(user_id, assigned_task_ids, timeline_ids)

    result = []
    for task in tasks:
        end = task.end_date.date() if hasattr(task.end_date, 'date') else task.end_date

        upcoming = end <= threshold
        if not upcoming and task.start_date:
            start = task.start_date.date() if hasattr(task.start_date, 'date') else task.start_date
            total = (end - start).days
            if total > 0 and (today - start).days / total >= 0.8:
                upcoming = True

        if upcoming:
            result.append(
                {
                    'task_id': task.task_id,
                    'name': task.name,
                    'end_date': end.isoformat(),
                    'priority': task.priority,
                    'timeline_id': task.timeline_id,
                    'is_overdue': end < today,
                    'type': 'task',
                }
            )

    return result


def get_task_members_with_contact(task_id: int) -> list[dict[str, Any]]:
    members, _ = build_task_member_list(task_id, include_contact=True)
    return members


def add_task_member_for_operator(
    task_id: int,
    operator_user_id: int,
    new_user_id: int,
    role: int = 1,
) -> None:
    task = get_task_by_id(task_id)
    if not task:
        raise TaskOperationError('找不到該任務', 404)

    if not can_manage_task_members(operator_user_id, task):
        raise TaskOperationError('只有負責人可新增成員', 403)

    if not new_user_id:
        raise TaskOperationError('請提供使用者 ID', 400)

    existing = get_task_member(task_id, new_user_id)
    if existing:
        raise TaskOperationError('該使用者已是任務成員', 409)

    with transaction(TaskOperationError, '成員新增失敗，請稍後再試'):
        task_member = TaskUser(task_id=task_id, user_id=new_user_id, role=role)
        add_entity(task_member)

        actor = get_user_by_id(operator_user_id)
        actor_name = actor.name if actor else '某人'
        task_name = task.name if task else '任務'

        create_notification(
            user_id=new_user_id,
            ntype='task_assigned',
            title=f'你被指派到任務「{task_name}」',
            content=f'{actor_name} 將你加入任務「{task_name}」',
            link='/tasks',
        )
    return {'message': '成員新增成功'}


def remove_task_member_for_owner(task_id: int, member_id: int) -> None:
    target = get_task_member(task_id, member_id)
    if target and target.role == 0:
        raise TaskOperationError('無法移除負責人', 400)

    with transaction(TaskOperationError, '成員移除失敗，請稍後再試'):
        remove_task_member(task_id, member_id)


def update_task_member_role_for_operator(
    task_id: int,
    member_id: int,
    new_role: int,
    operator_user_id: int,
) -> None:
    if new_role not in (0, 1):
        raise TaskOperationError('role 只允許 0(負責人) 或 1(協作者)', 400)

    task = get_task_by_id(task_id)
    if not task:
        raise TaskOperationError('找不到該任務', 404)

    if not can_manage_task_members(operator_user_id, task):
        raise TaskOperationError('只有任務負責人、任務建立者或專案負責人可執行此操作', 403)

    target = get_task_member(task_id, member_id)
    if target and target.role == 0 and new_role == 1:
        raise TaskOperationError('無法直接降級現任負責人，請先指定新負責人', 400)

    with transaction(TaskOperationError, '成員角色更新失敗，請稍後再試'):
        if not target:
            if task.timeline_id:
                timeline_member = get_timeline_member(task.timeline_id, member_id)
                if timeline_member is None:
                    raise TaskOperationError('該使用者不是此專案成員，無法設為主責人', 400)
            else:
                raise TaskOperationError('該使用者尚未加入任務，請先指派為成員', 400)

            target = TaskUser(task_id=task_id, user_id=member_id, role=1)
            add_entity(target)

        if new_role == 0:
            demote_task_members_to_collaborator(task_id)
            target.role = 0


def list_task_comments_for_member(task_id: int) -> list[dict[str, Any]]:
    comments = list_active_task_comments(task_id)

    result = []
    for comment in comments:
        user = get_user_by_id(comment.user_id)
        result.append(task_comment_to_dict(comment, user))
    return result


def add_task_comment_for_member(task_id: int, user_id: int, data: dict[str, Any]) -> int:
    message = data.get('message') or data.get('task_message')
    if not message:
        raise TaskOperationError('請提供留言內容', 400)

    with transaction(TaskOperationError, '留言新增失敗，請稍後再試'):
        comment = TaskComment(
            task_id=task_id,
            user_id=user_id,
            task_message=message,
        )
        add_entity(comment)

        actor = get_user_by_id(user_id)
        task = get_task_by_id(task_id)
        actor_name = actor.name if actor else '某人'
        task_name = task.name if task else '任務'

        members = list_task_members(task_id)
        notified_ids = {member.user_id for member in members} - {user_id}

        if not notified_ids and task and task.timeline_id:
            timeline_members = list_timeline_members(task.timeline_id)
            notified_ids = {member.user_id for member in timeline_members} - {user_id}

        for target_user_id in notified_ids:
            create_notification(
                user_id=target_user_id,
                ntype='comment',
                title=f'「{task_name}」有新留言',
                content=f'{actor_name}：{message[:50]}',
                link='/tasks',
            )

    user = get_user_by_id(user_id)
    return {
        'comment_id': comment.comment_id,
        'user_id': user_id,
        'user_name': user.name if user else '未知',
        'task_message': message,
        'created_at': comment.created_at.isoformat() + 'Z' if comment.created_at else None,
    }


def soft_delete_task_comment_for_user(task_id: int, comment_id: int, user_id: int) -> None:
    comment = get_active_task_comment(task_id, comment_id)

    if not comment:
        raise TaskOperationError('找不到該留言', 404)

    if comment.user_id != user_id:
        raise TaskOperationError('只能刪除自己的留言', 403)

    with transaction(TaskOperationError, '留言刪除失敗，請稍後再試'):
        comment.deleted_at = _utcnow_naive()


def list_subtasks_for_task(task_id: int) -> list[dict[str, Any]]:
    subtasks = list_subtasks(task_id)
    return [subtask.to_dict() for subtask in subtasks]


def create_subtask_for_task(task_id: int, name: str) -> int:
    if not name:
        raise TaskOperationError('請提供子任務名稱', 400)

    max_order = get_max_subtask_sort_order(task_id)

    with transaction(TaskOperationError, '子任務新增失敗，請稍後再試'):
        subtask = Subtask(
            task_id=task_id,
            name=name.strip(),
            sort_order=max_order + 1,
        )
        add_entity(subtask)
    return subtask.to_dict()


def _find_subtask_or_404(task_id, subtask_id):
    subtask = get_subtask(task_id, subtask_id)
    if not subtask:
        raise TaskOperationError('找不到該子任務', 404)
    return subtask


def update_subtask_for_task(task_id: int, subtask_id: int, data: dict[str, Any]) -> None:
    subtask = _find_subtask_or_404(task_id, subtask_id)

    with transaction(TaskOperationError, '子任務更新失敗，請稍後再試'):
        if 'name' in data:
            subtask.name = data['name']
        if 'completed' in data:
            subtask.completed = data['completed']
        if 'sort_order' in data:
            subtask.sort_order = data['sort_order']
    return subtask.to_dict()


def delete_subtask_for_task(task_id: int, subtask_id: int) -> None:
    subtask = _find_subtask_or_404(task_id, subtask_id)

    with transaction(TaskOperationError, '子任務刪除失敗，請稍後再試'):
        delete_entity(subtask)


def toggle_subtask_for_task(task_id: int, subtask_id: int) -> bool:
    subtask = _find_subtask_or_404(task_id, subtask_id)
    with transaction(TaskOperationError, '狀態更新失敗，請稍後再試'):
        subtask.completed = not subtask.completed
    return subtask.to_dict()


def update_task_status_for_member(task_id: int, new_status: str) -> None:
    task = _find_active_task_or_404(task_id)
    status_input = _validate_task_status_update_input(new_status)

    with transaction(TaskOperationError, '狀態更新失敗，請稍後再試'):
        task.change_status(status_input.status, completed_at_fallback=_utcnow_naive())
    return {
        'status': task.status,
        'completed': task.completed,
    }


def summarize_task_comments_for_member(task_id: int) -> dict[str, Any]:
    task = _find_active_task_or_404(task_id)

    comments = list_active_task_comments(task_id, ascending=True)

    if not comments:
        return {
            'task_id': task_id,
            'message': '目前尚無留言可摘要',
            'summary': {
                'decisions': [],
                'risks': [],
                'next_actions': [],
            },
            'meta': {
                'task_id': task_id,
                'comment_count': 0,
            },
        }

    comment_items = []
    for comment in comments:
        user = get_user_by_id(comment.user_id)
        comment_items.append(task_comment_to_dict(comment, user))

    try:
        summary, summary_meta = generate_task_comment_summary(task, comment_items)
        return {
            'task_id': task_id,
            'summary': summary,
            'meta': {
                'comment_count': len(comment_items),
                **summary_meta,
            },
        }
    except RuntimeError as exc:
        raise TaskOperationError(str(exc), 503) from exc
    except Exception as exc:
        raise TaskOperationError('AI 摘要失敗，請稍後再試', 500) from exc


def is_allowed_task_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_TASK_FILE_EXTENSIONS


def _task_upload_folder():
    return os.path.join(os.path.dirname(__file__), '..', 'uploads', 'task_files')


def _remove_file_if_exists(file_path):
    if not file_path or not os.path.exists(file_path):
        return
    try:
        os.remove(file_path)
    except OSError:
        pass


def _cleanup_task_upload_files(*file_paths):
    for file_path in file_paths:
        _remove_file_if_exists(file_path)


def list_task_files_for_member(task_id: int) -> list[dict[str, Any]]:
    files = list_task_files(task_id)
    result = []
    for task_file in files:
        uploader = get_user_by_id(task_file.uploaded_by)
        result.append(
            {
                'id': task_file.id,
                'filename': task_file.filename,
                'original_filename': task_file.original_filename,
                'file_size': task_file.file_size,
                'uploaded_at': task_file.uploaded_at.isoformat() + 'Z' if task_file.uploaded_at else None,
                'uploaded_by_name': uploader.name if uploader else '未知',
            }
        )
    return result


def upload_task_file_for_member(task_id: int, user_id: int, file_storage: Any) -> dict[str, Any]:
    if not file_storage or not file_storage.filename:
        raise TaskOperationError('檔案名稱為空', 400)

    if not is_allowed_task_file(file_storage.filename):
        raise TaskOperationError('不支援的檔案格式', 400)

    file_storage.seek(0, 2)
    file_size = file_storage.tell()
    file_storage.seek(0)
    if file_size > MAX_TASK_FILE_SIZE:
        raise TaskOperationError('檔案大小不可超過 10MB', 400)

    original_filename = file_storage.filename
    safe_filename = secure_filename(file_storage.filename)
    if not safe_filename or safe_filename.startswith('.'):
        ext = original_filename.rsplit('.', 1)[-1] if '.' in original_filename else 'bin'
        safe_filename = f'file.{ext}'

    upload_folder = _task_upload_folder()
    os.makedirs(upload_folder, exist_ok=True)

    unique_filename = f"{int(time.time())}_{safe_filename}"
    file_path = os.path.join(upload_folder, unique_filename)
    temp_file_path = f"{file_path}.tmp-{uuid.uuid4().hex}"
    file_storage.save(temp_file_path)

    task_file = TaskFile(
        task_id=task_id,
        filename=unique_filename,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        uploaded_by=user_id,
    )

    try:
        with transaction(TaskOperationError, '檔案上傳失敗，請稍後再試'):
            add_entity(task_file)
        os.replace(temp_file_path, file_path)
        return {
            'id': task_file.id,
            'message': '檔案上傳成功',
            'filename': unique_filename,
            'original_filename': original_filename,
            'file_size': file_size,
            'uploaded_at': task_file.uploaded_at.isoformat() + 'Z' if task_file.uploaded_at else None,
        }
    except Exception as exc:
        _cleanup_task_upload_files(temp_file_path, file_path)
        raise TaskOperationError('檔案上傳失敗，請稍後再試', 500) from exc


def delete_task_file_for_user(task_id: int, file_id: int, user_id: int) -> None:
    role = get_user_task_role(user_id, task_id)
    if role is None:
        raise TaskOperationError('你沒有權限存取此任務', 403)

    task_file = get_task_file(task_id, file_id)
    if not task_file:
        raise TaskOperationError('找不到該檔案', 404)

    if task_file.uploaded_by != user_id and role != 0:
        raise TaskOperationError('只有上傳者或負責人可刪除檔案', 403)

    file_path = task_file.file_path
    with transaction(TaskOperationError, '檔案刪除失敗，請稍後再試'):
        delete_entity(task_file)

    _remove_file_if_exists(file_path)


def resolve_task_file_download_for_user(filename: str, user_id: int) -> tuple[str, str]:
    task_file = get_task_file_by_filename(filename)
    if not task_file:
        raise TaskOperationError('找不到該檔案', 404)

    role = get_user_task_role(user_id, task_file.task_id)
    if role is None:
        raise TaskOperationError('你沒有權限存取此檔案', 403)

    original_name = task_file.original_filename if task_file.original_filename else filename
    return _task_upload_folder(), filename, original_name


def _to_clean_list(value, max_items=3):
    if isinstance(value, str):
        candidates = [value]
    elif isinstance(value, list):
        candidates = value
    else:
        candidates = []

    normalized = []
    for item in candidates:
        if not isinstance(item, str):
            continue
        cleaned = item.strip().strip('-').strip()
        if cleaned:
            normalized.append(cleaned)

    return normalized[:max_items]


def _normalize_summary_payload(payload, raw_text=None):
    if not isinstance(payload, dict):
        payload = {}

    normalized = {
        'decisions': _to_clean_list(payload.get('decisions')),
        'risks': _to_clean_list(payload.get('risks')),
        'next_actions': _to_clean_list(payload.get('next_actions')),
    }

    if isinstance(raw_text, str) and raw_text.strip():
        normalized['raw'] = raw_text.strip()

    return normalized


def _strip_markdown_fence(text):
    stripped = text.strip()
    if stripped.startswith('```'):
        stripped = re.sub(r'^```(?:json)?\s*', '', stripped, flags=re.IGNORECASE)
        stripped = re.sub(r'\s*```$', '', stripped)
    return stripped.strip()


def _extract_first_json_object(text):
    if not isinstance(text, str):
        return None

    start = text.find('{')
    if start < 0:
        return None

    depth = 0
    in_string = False
    escaped = False

    for i in range(start, len(text)):
        ch = text[i]

        if in_string:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]

    return None


def _parse_fallback_summary(raw_text):
    decisions = []
    risks = []
    next_actions = []

    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        decision_match = re.match(r'^(?:決議|決策|decisions?)\s*[:：]\s*(.+)$', stripped, flags=re.IGNORECASE)
        if decision_match:
            decisions.append(decision_match.group(1).strip())
            continue

        risk_match = re.match(r'^(?:風險|risks?)\s*[:：]\s*(.+)$', stripped, flags=re.IGNORECASE)
        if risk_match:
            risks.append(risk_match.group(1).strip())
            continue

        action_match = re.match(r'^(?:下一步|後續行動|next[_\s-]?actions?)\s*[:：]\s*(.+)$', stripped, flags=re.IGNORECASE)
        if action_match:
            next_actions.append(action_match.group(1).strip())

    return _normalize_summary_payload(
        {
            'decisions': decisions,
            'risks': risks,
            'next_actions': next_actions,
        },
        raw_text=raw_text,
    )


def build_task_comment_summary_context(
    task: Task,
    comment_items: list[TaskComment],
    max_chars: int = 12000,
) -> str:
    entries = []
    for item in comment_items:
        author = (item.get('user_name') or '未知使用者').strip()
        message = (item.get('task_message') or '').strip()
        created_at = (item.get('created_at') or '').replace('T', ' ').replace('Z', '')[:16]
        if not message:
            continue
        if created_at:
            entries.append(f"- [{created_at}] {author}: {message}")
        else:
            entries.append(f"- {author}: {message}")

    kept_entries_rev = []
    current_chars = 0
    for entry in reversed(entries):
        entry_len = len(entry) + 1
        if kept_entries_rev and current_chars + entry_len > max_chars:
            break

        if not kept_entries_rev and entry_len > max_chars:
            kept_entries_rev.append(entry[:max_chars])
            current_chars = max_chars
            break

        kept_entries_rev.append(entry)
        current_chars += entry_len

    kept_entries = list(reversed(kept_entries_rev))
    truncated = len(kept_entries) < len(entries)

    header_lines = [
        f"任務名稱: {task.name}",
        f"任務狀態: {task.status or 'pending'}",
        f"任務優先級: {task.priority if task.priority is not None else 2}",
        "",
        "留言紀錄（按時間排序）:",
    ]

    context = '\n'.join(header_lines + kept_entries)
    return context, {
        'total_comments': len(entries),
        'used_comments': len(kept_entries),
        'truncated': truncated,
        'context_chars': len(context),
    }


def generate_task_comment_summary(task: Task, comment_items: list[TaskComment]) -> dict[str, Any]:
    """使用可配置的 AI Provider 生成任務留言摘要（決議/風險/下一步）"""

    context, meta = build_task_comment_summary_context(task, comment_items)

    system_prompt = (
        '你是專案任務摘要助手。\n'
        '請依據提供的任務留言，輸出嚴格 JSON 格式，內容必須只有以下欄位：\n'
        '{"decisions": string[], "risks": string[], "next_actions": string[]}\n'
        '規則：\n'
        '1) 每個陣列最多 3 條\n'
        '2) 每條一句話，重點清楚\n'
        '3) 若沒有內容請回傳空陣列\n'
        '4) 不要輸出任何 JSON 以外文字'
    )

    user_message = f"留言內容：\n{context}"

    try:
        provider = get_ai_provider()
        raw_text = provider.generate_content(system_prompt, user_message, response_format="json")
    except RuntimeError as e:
        raise RuntimeError(str(e))

    cleaned = _strip_markdown_fence(raw_text) if isinstance(raw_text, str) else ''
    if not cleaned:
        raise RuntimeError('AI 摘要服務暫時不可用，請稍後再試')

    try:
        parsed_json = json.loads(cleaned)
        summary = _normalize_summary_payload(parsed_json, raw_text=cleaned)
    except json.JSONDecodeError:
        extracted_json = _extract_first_json_object(cleaned)
        if extracted_json:
            try:
                parsed_json = json.loads(extracted_json)
                summary = _normalize_summary_payload(parsed_json, raw_text=cleaned)
            except json.JSONDecodeError:
                summary = _parse_fallback_summary(cleaned)
        else:
            summary = _parse_fallback_summary(cleaned)

    # 記錄使用的 provider 類型
    provider_name = os.getenv("AI_PROVIDER", "gemini").lower()
    meta['provider'] = provider_name if provider_name in ["gemini", "mock"] else "gemini"
    return summary, meta
