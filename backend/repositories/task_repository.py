from sqlalchemy import or_

from models import db
from models.subtask import Subtask
from models.task import Task
from models.task_comment import TaskComment
from models.task_user import TaskUser
from models.timeline import TaskFile
from models.timeline_user import TimelineUser


def get_active_task_by_id(task_id):
    return Task.query.filter_by(task_id=task_id).filter(Task.deleted_at.is_(None)).first()


def get_task_by_id(task_id):
    return Task.query.filter_by(task_id=task_id).first()


def get_owned_active_tasks(user_id):
    return Task.query.filter_by(user_id=user_id).filter(Task.deleted_at.is_(None)).all()


def get_assigned_task_ids_for_user(user_id):
    return [task_user.task_id for task_user in TaskUser.query.filter_by(user_id=user_id).all()]


def get_timeline_ids_for_user(user_id):
    return [membership.timeline_id for membership in TimelineUser.query.filter_by(user_id=user_id).all()]


def get_active_tasks_by_ids(task_ids):
    if not task_ids:
        return []
    return Task.query.filter(Task.task_id.in_(task_ids), Task.deleted_at.is_(None)).all()


def get_task_member(task_id, user_id):
    return TaskUser.query.filter_by(task_id=task_id, user_id=user_id).first()


def list_task_members(task_id):
    return TaskUser.query.filter_by(task_id=task_id).all()


def remove_task_member(task_id, user_id):
    return TaskUser.query.filter_by(task_id=task_id, user_id=user_id).delete()


def demote_task_members_to_collaborator(task_id):
    return TaskUser.query.filter_by(task_id=task_id).update({'role': 1})


def get_timeline_membership_role(timeline_id, user_id):
    membership = TimelineUser.query.filter_by(timeline_id=timeline_id, user_id=user_id).first()
    return membership.role if membership else None


def get_timeline_member(timeline_id, user_id):
    return TimelineUser.query.filter_by(timeline_id=timeline_id, user_id=user_id).first()


def list_timeline_members(timeline_id):
    return TimelineUser.query.filter_by(timeline_id=timeline_id).all()


def get_upcoming_candidate_tasks_for_user(user_id, assigned_task_ids, timeline_ids):
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


def list_active_task_comments(task_id, ascending=False):
    query = (
        TaskComment.query
        .filter_by(task_id=task_id)
        .filter(TaskComment.deleted_at.is_(None))
    )

    if ascending:
        return query.order_by(TaskComment.created_at.asc()).all()
    return query.order_by(TaskComment.created_at.desc()).all()


def get_active_task_comment(task_id, comment_id):
    return (
        TaskComment.query
        .filter_by(comment_id=comment_id, task_id=task_id)
        .filter(TaskComment.deleted_at.is_(None))
        .first()
    )


def list_subtasks(task_id):
    return Subtask.query.filter_by(task_id=task_id).order_by(Subtask.sort_order).all()


def get_subtask(task_id, subtask_id):
    return Subtask.query.filter_by(id=subtask_id, task_id=task_id).first()


def get_max_subtask_sort_order(task_id):
    return db.session.query(db.func.max(Subtask.sort_order)).filter_by(task_id=task_id).scalar() or 0


def list_task_files(task_id):
    return TaskFile.query.filter_by(task_id=task_id).order_by(TaskFile.uploaded_at.desc()).all()


def get_task_file(task_id, file_id):
    return TaskFile.query.filter_by(id=file_id, task_id=task_id).first()


def get_task_file_by_filename(filename):
    return TaskFile.query.filter_by(filename=filename).first()
