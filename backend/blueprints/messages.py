from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.message import Message, MessageRead
from datetime import datetime
from services.message_service import get_unread_messages_query

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """取得未讀訊息數量"""
    user_id = int(get_jwt_identity())
    
    # 計算未讀訊息
    unread_count = get_unread_messages_query(user_id).count()
    
    return jsonify({'unread_count': unread_count}), 200

@messages_bp.route('/mark-all-read', methods=['POST'])
@jwt_required()
def mark_all_as_read():
    """標記所有訊息為已讀"""
    user_id = int(get_jwt_identity())
    
    # 找出所有未讀訊息
    unread_messages = get_unread_messages_query(user_id).all()
    
    # 標記為已讀
    for msg in unread_messages:
        read_record = MessageRead(
            message_id=msg.message_id,
            user_id=user_id,
            read_at=datetime.now()
        )
        db.session.add(read_record)
    
    try:
        db.session.commit()
        return jsonify({'message': '已標記所有訊息為已讀'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '標記訊息失敗，請稍後再試'}), 500
