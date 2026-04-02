from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.message_service import (
    MessageOperationError,
    get_unread_message_count,
    mark_all_unread_messages_as_read,
)

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """取得未讀訊息數量"""
    user_id = int(get_jwt_identity())

    unread_count = get_unread_message_count(user_id)

    return jsonify({'unread_count': unread_count}), 200

@messages_bp.route('/mark-all-read', methods=['POST'])
@jwt_required()
def mark_all_as_read():
    """標記所有訊息為已讀"""
    user_id = int(get_jwt_identity())

    try:
        mark_all_unread_messages_as_read(user_id)
        return jsonify({'message': '已標記所有訊息為已讀'}), 200
    except MessageOperationError as err:
        return jsonify({'error': err.message}), err.status_code
