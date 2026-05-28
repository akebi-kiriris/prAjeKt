import os
from typing import Any
from models.task import Task
from models.timeline import Timeline

from repositories.trash_repository import (
    get_deleted_task_by_owner,
    get_deleted_timeline_by_owner,
    list_deleted_member_tasks,
    list_deleted_member_timelines,
    list_deleted_owned_tasks,
    list_deleted_owned_timelines,
    list_member_task_ids,
    list_member_timeline_ids,
    list_tasks_by_timeline_id,
)
from repositories.session_repository import delete_entity
from services.transactions import transaction


class TrashOperationError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def trash_task_to_dict(task: Task, user_id: int) -> dict[str, Any]:
    return {
        'task_id': task.task_id,
        'name': task.name,
        'deleted_at': task.deleted_at.isoformat() + 'Z' if task.deleted_at else None,
        'end_date': task.end_date.isoformat() + 'Z' if task.end_date else None,
        'priority': task.priority,
        'is_owner': task.user_id == user_id,
    }


def trash_timeline_to_dict(timeline: Timeline, user_id: int) -> dict[str, Any]:
    return {
        'id': timeline.id,
        'name': timeline.name,
        'deleted_at': timeline.deleted_at.isoformat() + 'Z' if timeline.deleted_at else None,
        'start_date': timeline.start_date.isoformat() + 'Z' if timeline.start_date else None,
        'end_date': timeline.end_date.isoformat() + 'Z' if timeline.end_date else None,
        'is_owner': timeline.user_id == user_id,
    }


def remove_task_files(task: Task) -> None:
    for file_path in get_task_file_paths(task):
        remove_file_if_exists(file_path)


def get_task_file_paths(task: Task) -> list[str]:
    paths = []
    for task_file in task.files:
        if task_file.file_path:
            paths.append(task_file.file_path)
    return paths


def remove_file_if_exists(file_path: str | None) -> None:
    if file_path and os.path.exists(file_path):
        os.remove(file_path)


def get_trash_payload(user_id: int) -> dict[str, list[dict[str, Any]]]:
    own_deleted_tasks = list_deleted_owned_tasks(user_id)

    assigned_ids = list_member_task_ids(user_id)
    assigned_deleted = list_deleted_member_tasks(user_id, assigned_ids)

    tasks_result = [trash_task_to_dict(task, user_id) for task in own_deleted_tasks + assigned_deleted]

    own_deleted_timelines = list_deleted_owned_timelines(user_id)
    member_timeline_ids = list_member_timeline_ids(user_id)
    member_deleted_timelines = list_deleted_member_timelines(user_id, member_timeline_ids)

    timelines_result = [
        trash_timeline_to_dict(timeline, user_id)
        for timeline in own_deleted_timelines + member_deleted_timelines
    ]

    return {'tasks': tasks_result, 'timelines': timelines_result}


def restore_task_for_owner(task_id: int, user_id: int) -> None:
    task = get_deleted_task_by_owner(task_id, user_id)
    if not task:
        raise TrashOperationError('找不到該任務，或你沒有權限還原', 404)

    with transaction(TrashOperationError, '任務還原失敗，請稍後再試'):
        task.deleted_at = None


def permanently_delete_task_for_owner(task_id: int, user_id: int) -> None:
    task = get_deleted_task_by_owner(task_id, user_id)
    if not task:
        raise TrashOperationError('找不到該任務，或你沒有權限刪除', 404)

    file_paths = get_task_file_paths(task)
    with transaction(TrashOperationError, '任務永久刪除失敗，請稍後再試'):
        delete_entity(task)
    for file_path in file_paths:
        remove_file_if_exists(file_path)


def restore_timeline_for_owner(timeline_id: int, user_id: int) -> None:
    timeline = get_deleted_timeline_by_owner(timeline_id, user_id)
    if not timeline:
        raise TrashOperationError('找不到該專案，或你沒有權限還原', 404)

    with transaction(TrashOperationError, '專案還原失敗，請稍後再試'):
        timeline.deleted_at = None


def permanently_delete_timeline_for_owner(timeline_id: int, user_id: int) -> None:
    timeline = get_deleted_timeline_by_owner(timeline_id, user_id)
    if not timeline:
        raise TrashOperationError('找不到該專案，或你沒有權限刪除', 404)

    file_paths = []
    tasks = list_tasks_by_timeline_id(timeline_id)
    for task in tasks:
        file_paths.extend(get_task_file_paths(task))

    with transaction(TrashOperationError, '專案永久刪除失敗，請稍後再試'):
        for task in tasks:
            delete_entity(task)

        delete_entity(timeline)
    for file_path in file_paths:
        remove_file_if_exists(file_path)
