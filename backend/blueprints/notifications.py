from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.notification import Notification
from services.notification_service import notification_to_dict

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    """取得目前使用者的所有通知（最新 50 筆）"""
    user_id = int(get_jwt_identity())
    notifications = (
        Notification.query
        .filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify([notification_to_dict(n) for n in notifications]), 200


@notifications_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """取得未讀通知數量"""
    user_id = int(get_jwt_identity())
    count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    return jsonify({'count': count}), 200


@notifications_bp.route('/<int:notification_id>/read', methods=['PATCH'])
@jwt_required()
def mark_as_read(notification_id):
    """標記單筆通知為已讀"""
    user_id = int(get_jwt_identity())
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if not notification:
        return jsonify({'error': '找不到通知'}), 404
    notification.is_read = True
    db.session.commit()
    return jsonify({'message': '已標記為已讀'}), 200


@notifications_bp.route('/read-all', methods=['PATCH'])
@jwt_required()
def mark_all_as_read():
    """標記所有通知為已讀"""
    user_id = int(get_jwt_identity())
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'message': '全部標記為已讀'}), 200


@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """刪除單筆通知"""
    user_id = int(get_jwt_identity())
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if not notification:
        return jsonify({'error': '找不到通知'}), 404
    db.session.delete(notification)
    db.session.commit()
    return jsonify({'message': '通知已刪除'}), 200
