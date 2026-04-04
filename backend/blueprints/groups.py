from flask import Blueprint, request, jsonify, current_app
import os
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.group_service import (
    GroupOperationError,
    count_group_messages_for_snapshot,
    create_group_for_user,
    enqueue_snapshot_job,
    generate_group_snapshot,
    get_latest_group_snapshot_for_member,
    get_snapshot_job_status,
    get_snapshot_window_days_default,
    is_group_member,
    join_group_by_invite_code,
    leave_group_for_user,
    list_group_members_payload,
    list_group_messages_for_member,
    list_groups_for_user,
    send_group_message_for_member,
    should_enqueue_snapshot,
)

groups_bp = Blueprint('groups', __name__)


def _get_json_dict_or_400():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({'error': '請提供正確的 JSON 物件'}), 400)
    return data, None


def _parse_window_days(value):
    try:
        days = int(value)
    except (TypeError, ValueError):
        raise GroupOperationError('window_days 必須為正整數', 400)

    if days <= 0:
        raise GroupOperationError('window_days 必須為正整數', 400)

    return days


def _parse_async_flag(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'y'}
    if isinstance(value, (int, float)):
        return value != 0
    return False

@groups_bp.route('', methods=['GET'])
@jwt_required()
def get_groups():
    """取得使用者所屬的所有群組"""
    user_id = int(get_jwt_identity())

    return jsonify(list_groups_for_user(user_id)), 200

@groups_bp.route('', methods=['POST'])
@jwt_required()
def create_group():
    """建立新群組"""
    user_id = int(get_jwt_identity())
    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        payload = create_group_for_user(user_id, data.get('group_name', ''))
        return jsonify({
            'message': '任務小組已創建',
            'group_id': payload['group_id'],
            'invite_code': payload['invite_code'],
        }), 201
    except GroupOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@groups_bp.route('/join', methods=['POST'])
@jwt_required()
def join_group():
    """透過邀請碼加入群組"""
    user_id = int(get_jwt_identity())
    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        join_group_by_invite_code(user_id, data.get('invite_code', ''))
        return jsonify({'message': '成功加入群組'}), 200
    except GroupOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@groups_bp.route('/<int:group_id>/leave', methods=['POST'])
@jwt_required()
def leave_group(group_id):
    """離開群組"""
    user_id = int(get_jwt_identity())

    try:
        leave_group_for_user(group_id, user_id)
        return jsonify({'message': '已離開群組'}), 200
    except GroupOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@groups_bp.route('/<int:group_id>/members', methods=['GET'])
@jwt_required()
def get_group_members(group_id):
    """取得群組成員清單"""
    return jsonify(list_group_members_payload(group_id)), 200

@groups_bp.route('/<int:group_id>/messages', methods=['GET'])
@jwt_required()
def get_group_messages(group_id):
    """取得群組訊息"""
    user_id = int(get_jwt_identity())

    try:
        return jsonify(list_group_messages_for_member(group_id, user_id)), 200
    except GroupOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@groups_bp.route('/<int:group_id>/messages', methods=['POST'])
@jwt_required()
def send_message(group_id):
    """發送群組訊息"""
    user_id = int(get_jwt_identity())
    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        message_id = send_group_message_for_member(group_id, user_id, data.get('content', ''))
        return jsonify({'message': '訊息已發送', 'message_id': message_id}), 201
    except GroupOperationError as err:
        return jsonify({'error': err.message}), err.status_code


@groups_bp.route('/<int:group_id>/ai-snapshot', methods=['POST'])
@jwt_required()
def generate_ai_snapshot(group_id):
    """產生群組知識快照（小量同步，大量可背景執行）"""
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({'error': '請提供正確的 JSON 物件'}), 400

    try:
        if not is_group_member(group_id, user_id):
            raise GroupOperationError('您不是該群組成員', 403)

        window_days = _parse_window_days(data.get('window_days', get_snapshot_window_days_default()))
        async_requested = _parse_async_flag(data.get('async', False))

        source_count = count_group_messages_for_snapshot(group_id, window_days)
        if source_count == 0:
            raise GroupOperationError('最近沒有可摘要的群組訊息', 400)

        if should_enqueue_snapshot(source_count, async_requested):
            app_obj = current_app._get_current_object()
            job_payload = enqueue_snapshot_job(app_obj, group_id, user_id, window_days)
            return jsonify({
                'job_id': job_payload['job_id'],
                'status': job_payload['status'],
                'source_count': source_count,
                'threshold': int(os.getenv('SNAPSHOT_ASYNC_THRESHOLD', 500)),
            }), 202

        snapshot = generate_group_snapshot(
            group_id=group_id,
            window_days=window_days,
            created_by=user_id,
        )
        return jsonify(snapshot), 200
    except GroupOperationError as err:
        return jsonify({'error': err.message}), err.status_code


@groups_bp.route('/snapshot-jobs/<string:job_id>', methods=['GET'])
@jwt_required()
def get_ai_snapshot_job(job_id):
    """查詢群組知識快照背景工作狀態"""
    user_id = int(get_jwt_identity())

    try:
        payload = get_snapshot_job_status(job_id, requester_user_id=user_id)
        return jsonify(payload), 200
    except GroupOperationError as err:
        return jsonify({'error': err.message}), err.status_code


@groups_bp.route('/<int:group_id>/ai-snapshot/latest', methods=['GET'])
@jwt_required()
def get_latest_ai_snapshot(group_id):
    """取得群組最新知識快照"""
    user_id = int(get_jwt_identity())

    try:
        payload = get_latest_group_snapshot_for_member(group_id, user_id)
        return jsonify(payload), 200
    except GroupOperationError as err:
        return jsonify({'error': err.message}), err.status_code
