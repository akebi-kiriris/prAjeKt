from sqlalchemy import or_
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from models import db
from models.notification import Notification
from models.subtask import Subtask
from models.task import Task
from models.task_comment import TaskComment
from models.task_user import TaskUser
from models.timeline import TaskFile
from models.timeline_user import TimelineUser
from models.user import User


def get_active_task_by_id(task_id: int) -> Task | None:
    return Task.query.filter_by(task_id=task_id).filter(Task.deleted_at.is_(None)).first()


def get_task_by_id(task_id: int) -> Task | None:
    return Task.query.filter_by(task_id=task_id).first()


def get_owned_active_tasks(user_id: int) -> list[Task]:
    return Task.query.filter_by(user_id=user_id).filter(Task.deleted_at.is_(None)).all()


def get_assigned_task_ids_for_user(user_id: int) -> list[int]:
    return [task_user.task_id for task_user in TaskUser.query.filter_by(user_id=user_id).all()]


def get_timeline_ids_for_user(user_id: int) -> list[int]:
    return [membership.timeline_id for membership in TimelineUser.query.filter_by(user_id=user_id).all()]


def get_active_tasks_by_ids(task_ids: Sequence[int]) -> list[Task]:
    if not task_ids:
        return []
    return Task.query.filter(Task.task_id.in_(task_ids), Task.deleted_at.is_(None)).all()


def get_active_task_ids_for_timeline(timeline_id: int) -> list[int]:
    return [
        task.task_id
        for task in Task.query.filter(
            Task.timeline_id == timeline_id,
            Task.deleted_at.is_(None),
        ).all()
    ]


def get_task_member(task_id: int, user_id: int) -> TaskUser | None:
    return TaskUser.query.filter_by(task_id=task_id, user_id=user_id).first()


def list_task_members(task_id: int) -> list[TaskUser]:
    return TaskUser.query.filter_by(task_id=task_id).all()


def list_task_members_by_task_ids(task_ids: Sequence[int]) -> list[TaskUser]:
    if not task_ids:
        return []
    return TaskUser.query.filter(TaskUser.task_id.in_(task_ids)).all()


def remove_task_member(task_id: int, user_id: int) -> int:
    return TaskUser.query.filter_by(task_id=task_id, user_id=user_id).delete()


def demote_task_members_to_collaborator(task_id: int) -> int:
    return TaskUser.query.filter_by(task_id=task_id).update({'role': 1})


def get_timeline_membership_role(timeline_id: int, user_id: int) -> int | None:
    membership = TimelineUser.query.filter_by(timeline_id=timeline_id, user_id=user_id).first()
    return membership.role if membership else None


def get_timeline_member(timeline_id: int, user_id: int) -> TimelineUser | None:
    return TimelineUser.query.filter_by(timeline_id=timeline_id, user_id=user_id).first()


def list_timeline_members(timeline_id: int) -> list[TimelineUser]:
    return TimelineUser.query.filter_by(timeline_id=timeline_id).all()


def get_upcoming_candidate_tasks_for_user(
    user_id: int,
    assigned_task_ids: Sequence[int],
    timeline_ids: Sequence[int],
) -> list[Task]:
    conditions = [Task.user_id == user_id]
    if assigned_task_ids:
        conditions.append(Task.task_id.in_(assigned_task_ids))
    if timeline_ids:
        conditions.append(Task.timeline_id.in_(timeline_ids))

    return Task.query.filter(
        Task.deleted_at.is_(None),
        Task.completed == False,
        Task.end_date.isnot(None),
        or_(*conditions),
    ).all()


def list_active_task_comments(task_id: int, ascending: bool = False) -> list[TaskComment]:
    query = (
        TaskComment.query
        .filter_by(task_id=task_id)
        .filter(TaskComment.deleted_at.is_(None))
    )

    if ascending:
        return query.order_by(TaskComment.created_at.asc()).all()
    return query.order_by(TaskComment.created_at.desc()).all()


def get_active_task_comment(task_id: int, comment_id: int) -> TaskComment | None:
    return (
        TaskComment.query
        .filter_by(comment_id=comment_id, task_id=task_id)
        .filter(TaskComment.deleted_at.is_(None))
        .first()
    )


def list_subtasks(task_id: int) -> list[Subtask]:
    return Subtask.query.filter_by(task_id=task_id).order_by(Subtask.sort_order).all()


def list_subtasks_by_task_ids(task_ids: Sequence[int]) -> list[Subtask]:
    if not task_ids:
        return []
    return (
        Subtask.query
        .filter(Subtask.task_id.in_(task_ids))
        .order_by(Subtask.task_id.asc(), Subtask.sort_order.asc())
        .all()
    )


def get_subtask(task_id: int, subtask_id: int) -> Subtask | None:
    return Subtask.query.filter_by(id=subtask_id, task_id=task_id).first()


def get_max_subtask_sort_order(task_id: int) -> int:
    return db.session.query(db.func.max(Subtask.sort_order)).filter_by(task_id=task_id).scalar() or 0


def list_task_files(task_id: int) -> list[TaskFile]:
    return TaskFile.query.filter_by(task_id=task_id).order_by(TaskFile.uploaded_at.desc()).all()


def get_task_file(task_id: int, file_id: int) -> TaskFile | None:
    return TaskFile.query.filter_by(id=file_id, task_id=task_id).first()


def get_task_file_by_filename(filename: str) -> TaskFile | None:
    return TaskFile.query.filter_by(filename=filename).first()


def get_users_by_ids(user_ids: Sequence[int]) -> list[User]:
    if not user_ids:
        return []
    return User.query.filter(User.id.in_(list(user_ids))).all()


def get_user_by_id(user_id: int) -> User | None:
    return db.session.get(User, user_id)


def build_task_entity(
    *,
    user_id: int,
    name: str,
    timeline_id: int | None,
    priority: int,
    status: str,
    tags: str | None,
    estimated_hours: float | int | None,
    start_date: datetime | None,
    end_date: datetime | None,
    task_remark: str | None,
    is_work: int,
    depends_on_task_ids: list[int] | None,
) -> Task:
    return Task(
        user_id=user_id,
        name=name,
        completed=False,
        completed_at=None,
        timeline_id=timeline_id,
        priority=priority,
        status=status,
        tags=tags,
        estimated_hours=estimated_hours,
        start_date=start_date,
        end_date=end_date,
        task_remark=task_remark,
        isWork=is_work,
        depends_on_task_ids=depends_on_task_ids,
    )


def build_task_member_entity(task_id: int, user_id: int, role: int) -> TaskUser:
    return TaskUser(task_id=task_id, user_id=user_id, role=role)


def build_notification_entity(
    *,
    user_id: int,
    ntype: str,
    title: str,
    content: str | None = None,
    link: str | None = None,
) -> Notification:
    return Notification(
        user_id=user_id,
        type=ntype,
        title=title,
        content=content,
        link=link,
    )
