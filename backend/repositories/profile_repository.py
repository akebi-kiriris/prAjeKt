from sqlalchemy import or_
from collections.abc import Sequence

from models import db
from models.task import Task
from models.task_user import TaskUser
from models.timeline import Timeline
from models.timeline_user import TimelineUser
from models.user import User


def get_user_by_id(user_id: int) -> User | None:
    return db.session.get(User, user_id)


def get_user_by_username_excluding_id(username: str, user_id: int) -> User | None:
    return User.query.filter(User.username == username, User.id != user_id).first()


def get_user_by_email_excluding_id(email: str, user_id: int) -> User | None:
    return User.query.filter(User.email == email, User.id != user_id).first()


def search_user_by_username_or_email(query: str) -> User | None:
    return User.query.filter(or_(User.username == query, User.email == query)).first()


def list_timeline_ids_for_user(user_id: int) -> list[int]:
    return [member.timeline_id for member in TimelineUser.query.filter_by(user_id=user_id).all()]


def list_direct_task_ids_for_user(user_id: int) -> list[int]:
    return [member.task_id for member in TaskUser.query.filter_by(user_id=user_id).all()]


def list_active_tasks_for_user_scope(
    user_id: int,
    direct_task_ids: Sequence[int],
    timeline_ids: Sequence[int],
) -> list[Task]:
    conditions = [Task.user_id == user_id]
    if direct_task_ids:
        conditions.append(Task.task_id.in_(direct_task_ids))
    if timeline_ids:
        conditions.append(Task.timeline_id.in_(timeline_ids))

    return Task.query.filter(
        Task.deleted_at.is_(None),
        or_(*conditions),
    ).all()


def list_active_timelines_by_ids(timeline_ids: Sequence[int]) -> list[Timeline]:
    if not timeline_ids:
        return []

    return Timeline.query.filter(
        Timeline.id.in_(timeline_ids),
        Timeline.deleted_at.is_(None),
    ).all()
