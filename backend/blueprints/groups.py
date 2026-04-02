from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.group_service import (
    GroupOperationError,
    create_group_for_user,
    join_group_by_invite_code,
    leave_group_for_user,
    list_group_members_payload,
    list_group_messages_for_member,
    list_groups_for_user,
    send_group_message_for_member,
)

groups_bp = Blueprint('groups', __name__)


def _get_json_dict_or_400():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({'error': '請提供正確的 JSON 物件'}), 400)
    return data, None

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
