from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.trash_service import (
    TrashOperationError,
    get_trash_payload,
    permanently_delete_task_for_owner,
    permanently_delete_timeline_for_owner,
    restore_task_for_owner,
    restore_timeline_for_owner,
)

trash_bp = Blueprint('trash', __name__)


# ─────────────── 查詢垃圾桶 ───────────────

@trash_bp.route('', methods=['GET'])
@jwt_required()
def get_trash():
    """取得當前使用者垃圾桶內容（已軟刪除的任務 + 專案）"""
    user_id = int(get_jwt_identity())
    return jsonify(get_trash_payload(user_id)), 200


# ─────────────── 任務：還原 / 永久刪除 ───────────────

@trash_bp.route('/tasks/<int:task_id>/restore', methods=['PATCH'])
@jwt_required()
def restore_task(task_id):
    """還原已刪除的任務（僅建立者可操作）"""
    user_id = int(get_jwt_identity())
    try:
        restore_task_for_owner(task_id, user_id)
        return jsonify({'message': '任務已還原'}), 200
    except TrashOperationError as err:
        return jsonify({'error': err.message}), err.status_code


@trash_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def permanently_delete_task(task_id):
    """永久刪除任務（僅建立者可操作，同時刪除磁碟上的附件）"""
    user_id = int(get_jwt_identity())
    try:
        permanently_delete_task_for_owner(task_id, user_id)
        return jsonify({'message': '任務已永久刪除'}), 200
    except TrashOperationError as err:
        return jsonify({'error': err.message}), err.status_code


# ─────────────── 專案：還原 / 永久刪除 ───────────────

@trash_bp.route('/timelines/<int:timeline_id>/restore', methods=['PATCH'])
@jwt_required()
def restore_timeline(timeline_id):
    """還原已刪除的專案（僅建立者可操作）"""
    user_id = int(get_jwt_identity())
    try:
        restore_timeline_for_owner(timeline_id, user_id)
        return jsonify({'message': '專案已還原'}), 200
    except TrashOperationError as err:
        return jsonify({'error': err.message}), err.status_code


@trash_bp.route('/timelines/<int:timeline_id>', methods=['DELETE'])
@jwt_required()
def permanently_delete_timeline(timeline_id):
    """永久刪除專案（僅建立者可操作）
    流程：先刪所有子任務的磁碟附件，再刪 Task（cascade 清留言/成員/附件記錄），最後刪 Timeline（cascade 清成員）
    """
    user_id = int(get_jwt_identity())
    try:
        permanently_delete_timeline_for_owner(timeline_id, user_id)
        return jsonify({'message': '專案已永久刪除'}), 200
    except TrashOperationError as err:
        return jsonify({'error': err.message}), err.status_code
