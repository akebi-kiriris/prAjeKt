from sqlalchemy import or_

from models import db
from models.task import Task
from models.task_comment import TaskComment
from models.task_user import TaskUser
from models.timeline import Timeline
from models.timeline_user import TimelineUser
from models.user import User


def get_active_timeline_by_id(timeline_id):
    return Timeline.query.filter_by(id=timeline_id).filter(Timeline.deleted_at.is_(None)).first()


def get_timeline_memberships_for_user(user_id):
    return (
        db.session.query(Timeline, TimelineUser.role)
        .join(TimelineUser, Timeline.id == TimelineUser.timeline_id)
        .filter(TimelineUser.user_id == user_id, Timeline.deleted_at.is_(None))
        .all()
    )


def get_timeline_memberships_for_user_ordered_desc(user_id):
    return (
        db.session.query(Timeline, TimelineUser.role)
        .join(TimelineUser, Timeline.id == TimelineUser.timeline_id)
        .filter(TimelineUser.user_id == user_id, Timeline.deleted_at.is_(None))
        .order_by(Timeline.id.desc())
        .all()
    )


def get_active_tasks_by_timeline_id(timeline_id):
    return Task.query.filter_by(timeline_id=timeline_id).filter(Task.deleted_at.is_(None)).all()


def get_active_tasks_by_timeline_ids(timeline_ids):
    if not timeline_ids:
        return []

    return Task.query.filter(
        Task.timeline_id.in_(timeline_ids),
        Task.deleted_at.is_(None),
    ).all()


def get_active_incomplete_tasks_by_timeline_id(timeline_id):
    return (
        Task.query.filter_by(timeline_id=timeline_id)
        .filter(
            Task.deleted_at.is_(None),
            Task.completed.is_(False),
        )
        .all()
    )


def get_active_tasks_by_timeline_id_ordered_end_date(timeline_id):
    return (
        Task.query.filter_by(timeline_id=timeline_id)
        .filter(Task.deleted_at.is_(None))
        .order_by(Task.end_date)
        .all()
    )


def get_timeline_members(timeline_id):
    return TimelineUser.query.filter_by(timeline_id=timeline_id).all()


def get_timeline_member(timeline_id, user_id):
    return TimelineUser.query.filter_by(timeline_id=timeline_id, user_id=user_id).first()


def get_timeline_role(timeline_id, user_id):
    member = get_timeline_member(timeline_id, user_id)
    return member.role if member is not None else None


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def get_user_by_id(user_id):
    return db.session.get(User, user_id)


def get_task_users_by_task_ids(task_ids):
    if not task_ids:
        return []
    return TaskUser.query.filter(TaskUser.task_id.in_(task_ids)).all()


def get_task_user_membership(task_id, user_id):
    return TaskUser.query.filter_by(task_id=task_id, user_id=user_id).first()


def get_users_by_ids(user_ids):
    if not user_ids:
        return []
    return User.query.filter(User.id.in_(user_ids)).all()


def get_active_timelines_by_ids(timeline_ids):
    if not timeline_ids:
        return []
    return Timeline.query.filter(
        Timeline.id.in_(timeline_ids),
        Timeline.deleted_at.is_(None),
    ).all()


def get_timeline_by_id(timeline_id):
    return db.session.get(Timeline, timeline_id)


def build_timeline_entity(*, user_id, name, start_date, end_date, remark):
    return Timeline(
        user_id=user_id,
        name=name,
        start_date=start_date,
        end_date=end_date,
        remark=remark,
    )


def build_timeline_member_entity(*, timeline_id, user_id, role):
    return TimelineUser(timeline_id=timeline_id, user_id=user_id, role=role)


def soft_delete_tasks_by_timeline_id(timeline_id, deleted_at):
    return Task.query.filter_by(timeline_id=timeline_id).update(
        {'deleted_at': deleted_at},
        synchronize_session=False,
    )


def soft_delete_tasks_by_ids(task_ids, deleted_at):
    if not task_ids:
        return 0

    return Task.query.filter(Task.task_id.in_(task_ids)).update(
        {'deleted_at': deleted_at},
        synchronize_session=False,
    )


def list_recent_task_comments_for_timeline_period(timeline_id, period_start_dt, period_end_dt, limit=20):
    return (
        TaskComment.query.join(Task, Task.task_id == TaskComment.task_id)
        .filter(
            Task.timeline_id == timeline_id,
            Task.deleted_at.is_(None),
            TaskComment.deleted_at.is_(None),
            TaskComment.created_at >= period_start_dt,
            TaskComment.created_at < period_end_dt,
        )
        .order_by(TaskComment.created_at.desc())
        .limit(limit)
        .all()
    )


def list_task_ids_by_assignee_user_id(user_id):
    return [task_user.task_id for task_user in TaskUser.query.filter(TaskUser.user_id == user_id).all()]


def list_task_ids_by_assignee_user_id_within(user_id, task_ids):
    if not task_ids:
        return []

    return [
        task_user.task_id
        for task_user in TaskUser.query.filter(
            TaskUser.user_id == user_id,
            TaskUser.task_id.in_(task_ids),
        ).all()
    ]


def list_cross_project_active_tasks_for_assignee(
    assignee_user_id,
    current_timeline_id,
    assignee_task_id_set,
    excluded_task_id=None,
    window_start=None,
    window_end=None,
):
    query = Task.query.filter(
        Task.deleted_at.is_(None),
        Task.completed == False,
        Task.timeline_id.isnot(None),
        Task.timeline_id != current_timeline_id,
    )

    if window_start is not None and window_end is not None:
        query = query.filter(
            Task.start_date.isnot(None),
            Task.end_date.isnot(None),
            Task.start_date <= window_end,
            Task.end_date >= window_start,
        )

    if assignee_task_id_set:
        query = query.filter(
            or_(
                Task.user_id == assignee_user_id,
                Task.task_id.in_(assignee_task_id_set),
            )
        )
    else:
        query = query.filter(Task.user_id == assignee_user_id)

    if excluded_task_id is not None:
        query = query.filter(Task.task_id != excluded_task_id)

    return query.all()


def list_active_tasks_for_assignee(
    assignee_user_id,
    assignee_task_id_set,
    excluded_task_id=None,
    window_start=None,
    window_end=None,
):
    query = Task.query.filter(
        Task.deleted_at.is_(None),
        Task.completed == False,
        Task.timeline_id.isnot(None),
    )

    if window_start is not None and window_end is not None:
        query = query.filter(
            Task.start_date.isnot(None),
            Task.end_date.isnot(None),
            Task.start_date <= window_end,
            Task.end_date >= window_start,
        )

    if assignee_task_id_set:
        query = query.filter(
            or_(
                Task.user_id == assignee_user_id,
                Task.task_id.in_(assignee_task_id_set),
            )
        )
    else:
        query = query.filter(Task.user_id == assignee_user_id)

    if excluded_task_id is not None:
        query = query.filter(Task.task_id != excluded_task_id)

    return query.all()


def build_timeline_task_entity(
    *,
    user_id,
    timeline_id,
    name,
    priority,
    status,
    task_remark,
    start_date,
    end_date,
    is_work=1,
):
    return Task(
        user_id=user_id,
        timeline_id=timeline_id,
        name=name,
        priority=priority,
        status=status,
        task_remark=task_remark,
        start_date=start_date,
        end_date=end_date,
        completed=False,
        isWork=is_work,
    )
