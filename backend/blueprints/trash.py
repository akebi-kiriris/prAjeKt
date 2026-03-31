from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.task import Task
from models.timeline import Timeline, TaskFile
from models.task_user import TaskUser
from models.timeline_user import TimelineUser
from services.trash_service import trash_task_to_dict, trash_timeline_to_dict, remove_task_files

trash_bp = Blueprint('trash', __name__)


# ─────────────── 查詢垃圾桶 ───────────────

@trash_bp.route('', methods=['GET'])
@jwt_required()
def get_trash():
    """取得當前使用者垃圾桶內容（已軟刪除的任務 + 專案）"""
    user_id = int(get_jwt_identity())

    # 已刪除的任務：自己建立的 + 被指派且已刪除的
    own_deleted_tasks = Task.query.filter_by(user_id=user_id).filter(Task.deleted_at.isnot(None)).all()
    # 同時也查詢其他人刪除但自己是成員的任務（只顯示，無法還原）
    assigned_ids = [tu.task_id for tu in TaskUser.query.filter_by(user_id=user_id).all()]
    assigned_deleted = Task.query.filter(
        Task.task_id.in_(assigned_ids),
        Task.deleted_at.isnot(None),
        Task.user_id != user_id  # 排除自己建立的（已在 own_deleted_tasks）
    ).all() if assigned_ids else []

    tasks_result = [
        trash_task_to_dict(t, user_id)
        for t in own_deleted_tasks + assigned_deleted
    ]

    # 已刪除的專案：自己建立的 + 自己是成員的
    own_deleted_timelines = Timeline.query.filter_by(user_id=user_id).filter(Timeline.deleted_at.isnot(None)).all()
    member_timeline_ids = [tu.timeline_id for tu in TimelineUser.query.filter_by(user_id=user_id).all()]
    member_deleted_timelines = Timeline.query.filter(
        Timeline.id.in_(member_timeline_ids),
        Timeline.deleted_at.isnot(None),
        Timeline.user_id != user_id
    ).all() if member_timeline_ids else []

    timelines_result = [
        trash_timeline_to_dict(tl, user_id)
        for tl in own_deleted_timelines + member_deleted_timelines
    ]

    return jsonify({'tasks': tasks_result, 'timelines': timelines_result}), 200


# ─────────────── 任務：還原 / 永久刪除 ───────────────

@trash_bp.route('/tasks/<int:task_id>/restore', methods=['PATCH'])
@jwt_required()
def restore_task(task_id):
    """還原已刪除的任務（僅建立者可操作）"""
    user_id = int(get_jwt_identity())
    task = Task.query.filter_by(task_id=task_id, user_id=user_id).filter(Task.deleted_at.isnot(None)).first()
    if not task:
        return jsonify({'error': '找不到該任務，或你沒有權限還原'}), 404
    try:
        task.deleted_at = None
        db.session.commit()
        return jsonify({'message': '任務已還原'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '任務還原失敗，請稍後再試'}), 500


@trash_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def permanently_delete_task(task_id):
    """永久刪除任務（僅建立者可操作，同時刪除磁碟上的附件）"""
    user_id = int(get_jwt_identity())
    task = Task.query.filter_by(task_id=task_id, user_id=user_id).filter(Task.deleted_at.isnot(None)).first()
    if not task:
        return jsonify({'error': '找不到該任務，或你沒有權限刪除'}), 404
    try:
        # 刪除磁碟上的附件檔案（DB 記錄由 cascade 自動清除）
        remove_task_files(task)
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': '任務已永久刪除'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '任務永久刪除失敗，請稍後再試'}), 500


# ─────────────── 專案：還原 / 永久刪除 ───────────────

@trash_bp.route('/timelines/<int:timeline_id>/restore', methods=['PATCH'])
@jwt_required()
def restore_timeline(timeline_id):
    """還原已刪除的專案（僅建立者可操作）"""
    user_id = int(get_jwt_identity())
    timeline = Timeline.query.filter_by(id=timeline_id, user_id=user_id).filter(Timeline.deleted_at.isnot(None)).first()
    if not timeline:
        return jsonify({'error': '找不到該專案，或你沒有權限還原'}), 404
    try:
        timeline.deleted_at = None
        db.session.commit()
        return jsonify({'message': '專案已還原'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '專案還原失敗，請稍後再試'}), 500


@trash_bp.route('/timelines/<int:timeline_id>', methods=['DELETE'])
@jwt_required()
def permanently_delete_timeline(timeline_id):
    """永久刪除專案（僅建立者可操作）
    流程：先刪所有子任務的磁碟附件，再刪 Task（cascade 清留言/成員/附件記錄），最後刪 Timeline（cascade 清成員）
    """
    user_id = int(get_jwt_identity())
    timeline = Timeline.query.filter_by(id=timeline_id, user_id=user_id).filter(Timeline.deleted_at.isnot(None)).first()
    if not timeline:
        return jsonify({'error': '找不到該專案，或你沒有權限刪除'}), 404
    try:
        # 取得該 timeline 下所有任務（含未軟刪除的）
        tasks = Task.query.filter_by(timeline_id=timeline_id).all()
        for task in tasks:
            remove_task_files(task)
            db.session.delete(task)  # cascade 清 comments / task_users / subtasks / task_files

        db.session.delete(timeline)  # cascade 清 timeline_users
        db.session.commit()
        return jsonify({'message': '專案已永久刪除'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '專案永久刪除失敗，請稍後再試'}), 500
