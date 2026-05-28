from models.task import Task
from models.task_user import TaskUser
from models.timeline import Timeline
from models.timeline_user import TimelineUser
from collections.abc import Sequence


def list_deleted_owned_tasks(user_id: int) -> list[Task]:
    return Task.query.filter_by(user_id=user_id).filter(Task.deleted_at.isnot(None)).all()


def list_member_task_ids(user_id: int) -> list[int]:
    return [member.task_id for member in TaskUser.query.filter_by(user_id=user_id).all()]


def list_deleted_member_tasks(user_id: int, task_ids: Sequence[int]) -> list[Task]:
    if not task_ids:
        return []

    return Task.query.filter(
        Task.task_id.in_(task_ids),
        Task.deleted_at.isnot(None),
        Task.user_id != user_id,
    ).all()


def list_deleted_owned_timelines(user_id: int) -> list[Timeline]:
    return Timeline.query.filter_by(user_id=user_id).filter(Timeline.deleted_at.isnot(None)).all()


def list_member_timeline_ids(user_id: int) -> list[int]:
    return [member.timeline_id for member in TimelineUser.query.filter_by(user_id=user_id).all()]


def list_deleted_member_timelines(user_id: int, timeline_ids: Sequence[int]) -> list[Timeline]:
    if not timeline_ids:
        return []

    return Timeline.query.filter(
        Timeline.id.in_(timeline_ids),
        Timeline.deleted_at.isnot(None),
        Timeline.user_id != user_id,
    ).all()


def get_deleted_task_by_owner(task_id: int, user_id: int) -> Task | None:
    return Task.query.filter_by(task_id=task_id, user_id=user_id).filter(Task.deleted_at.isnot(None)).first()


def get_deleted_timeline_by_owner(timeline_id: int, user_id: int) -> Timeline | None:
    return Timeline.query.filter_by(id=timeline_id, user_id=user_id).filter(Timeline.deleted_at.isnot(None)).first()


def list_tasks_by_timeline_id(timeline_id: int) -> list[Task]:
    return Task.query.filter_by(timeline_id=timeline_id).all()
