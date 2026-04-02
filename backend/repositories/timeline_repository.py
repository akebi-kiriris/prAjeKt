from models import db
from models.task import Task
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


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def get_user_by_id(user_id):
    return db.session.get(User, user_id)


def get_task_users_by_task_ids(task_ids):
    if not task_ids:
        return []
    return TaskUser.query.filter(TaskUser.task_id.in_(task_ids)).all()


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
