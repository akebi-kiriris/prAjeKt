import os

from models import db
from models.task import Task
from models.task_user import TaskUser
from models.timeline import Timeline
from models.timeline_user import TimelineUser


class TrashOperationError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def trash_task_to_dict(task, user_id):
    return {
        'task_id': task.task_id,
        'name': task.name,
        'deleted_at': task.deleted_at.isoformat() + 'Z' if task.deleted_at else None,
        'end_date': task.end_date.isoformat() + 'Z' if task.end_date else None,
        'priority': task.priority,
        'is_owner': task.user_id == user_id,
    }


def trash_timeline_to_dict(timeline, user_id):
    return {
        'id': timeline.id,
        'name': timeline.name,
        'deleted_at': timeline.deleted_at.isoformat() + 'Z' if timeline.deleted_at else None,
        'start_date': timeline.start_date.isoformat() + 'Z' if timeline.start_date else None,
        'end_date': timeline.end_date.isoformat() + 'Z' if timeline.end_date else None,
        'is_owner': timeline.user_id == user_id,
    }


def remove_task_files(task):
    for task_file in task.files:
        if task_file.file_path and os.path.exists(task_file.file_path):
            os.remove(task_file.file_path)


def get_trash_payload(user_id):
    own_deleted_tasks = Task.query.filter_by(user_id=user_id).filter(Task.deleted_at.isnot(None)).all()

    assigned_ids = [tu.task_id for tu in TaskUser.query.filter_by(user_id=user_id).all()]
    assigned_deleted = (
        Task.query.filter(
            Task.task_id.in_(assigned_ids),
            Task.deleted_at.isnot(None),
            Task.user_id != user_id,
        ).all()
        if assigned_ids
        else []
    )

    tasks_result = [trash_task_to_dict(task, user_id) for task in own_deleted_tasks + assigned_deleted]

    own_deleted_timelines = Timeline.query.filter_by(user_id=user_id).filter(Timeline.deleted_at.isnot(None)).all()
    member_timeline_ids = [tu.timeline_id for tu in TimelineUser.query.filter_by(user_id=user_id).all()]
    member_deleted_timelines = (
        Timeline.query.filter(
            Timeline.id.in_(member_timeline_ids),
            Timeline.deleted_at.isnot(None),
            Timeline.user_id != user_id,
        ).all()
        if member_timeline_ids
        else []
    )

    timelines_result = [
        trash_timeline_to_dict(timeline, user_id)
        for timeline in own_deleted_timelines + member_deleted_timelines
    ]

    return {'tasks': tasks_result, 'timelines': timelines_result}


def restore_task_for_owner(task_id, user_id):
    task = Task.query.filter_by(task_id=task_id, user_id=user_id).filter(Task.deleted_at.isnot(None)).first()
    if not task:
        raise TrashOperationError('找不到該任務，或你沒有權限還原', 404)

    try:
        task.deleted_at = None
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise TrashOperationError('任務還原失敗，請稍後再試', 500) from exc


def permanently_delete_task_for_owner(task_id, user_id):
    task = Task.query.filter_by(task_id=task_id, user_id=user_id).filter(Task.deleted_at.isnot(None)).first()
    if not task:
        raise TrashOperationError('找不到該任務，或你沒有權限刪除', 404)

    try:
        remove_task_files(task)
        db.session.delete(task)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise TrashOperationError('任務永久刪除失敗，請稍後再試', 500) from exc


def restore_timeline_for_owner(timeline_id, user_id):
    timeline = Timeline.query.filter_by(id=timeline_id, user_id=user_id).filter(Timeline.deleted_at.isnot(None)).first()
    if not timeline:
        raise TrashOperationError('找不到該專案，或你沒有權限還原', 404)

    try:
        timeline.deleted_at = None
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise TrashOperationError('專案還原失敗，請稍後再試', 500) from exc


def permanently_delete_timeline_for_owner(timeline_id, user_id):
    timeline = Timeline.query.filter_by(id=timeline_id, user_id=user_id).filter(Timeline.deleted_at.isnot(None)).first()
    if not timeline:
        raise TrashOperationError('找不到該專案，或你沒有權限刪除', 404)

    try:
        tasks = Task.query.filter_by(timeline_id=timeline_id).all()
        for task in tasks:
            remove_task_files(task)
            db.session.delete(task)

        db.session.delete(timeline)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise TrashOperationError('專案永久刪除失敗，請稍後再試', 500) from exc
