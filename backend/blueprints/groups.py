from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models.group import Group, GroupMember
from models.message import Message
import random

groups_bp = Blueprint('groups', __name__)

@groups_bp.route('', methods=['GET'])
@jwt_required()
def get_groups():
    """取得使用者所屬的所有群組"""
    user_id = int(get_jwt_identity())
    
    groups = db.session.query(Group).join(
        GroupMember, Group.group_id == GroupMember.group_id
    ).filter(GroupMember.user_id == user_id).all()
    
    return jsonify([{
        'group_id': g.group_id,
        'group_name': g.group_name,
        'group_type': g.group_type,
        'invite_code': g.group_inviteCode,
        'created_at': g.created_at.isoformat() if g.created_at else None
    } for g in groups]), 200

@groups_bp.route('', methods=['POST'])
@jwt_required()
def create_group():
    """建立新群組"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    group_name = data.get('group_name', '').strip()
    if not group_name:
        return jsonify({'error': '請輸入群組名稱'}), 400
    
    # 生成隨機六位數邀請碼
    while True:
        invite_code = f"{random.randint(0, 999999):06d}"
        existing = Group.query.filter_by(group_inviteCode=invite_code).first()
        if not existing:
            break
    
    new_group = Group(
        group_name=group_name,
        group_type='task',
        group_inviteCode=invite_code
    )
    
    try:
        db.session.add(new_group)
        db.session.flush()  # ?��? group_id
        
        # 將創建者加入群組
        member = GroupMember(group_id=new_group.group_id, user_id=user_id)
        db.session.add(member)
        db.session.commit()
        
        return jsonify({
            'message': '任務小組已創建',
            'group_id': new_group.group_id,
            'invite_code': invite_code
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/join', methods=['POST'])
@jwt_required()
def join_group():
    """透過邀請碼加入群組"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    invite_code = data.get('invite_code', '').strip()
    if not invite_code:
        return jsonify({'error': '請輸入邀請碼'}), 400
    
    group = Group.query.filter_by(group_inviteCode=invite_code).first()
    if not group:
        return jsonify({'error': '邀請碼無效'}), 404
    
    # 檢查是否已加入
    existing = GroupMember.query.filter_by(group_id=group.group_id, user_id=user_id).first()
    if existing:
        return jsonify({'error': '您已經是該群組成員'}), 409
    
    member = GroupMember(group_id=group.group_id, user_id=user_id)
    
    try:
        db.session.add(member)
        db.session.commit()
        return jsonify({'message': '成功加入群組'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/<int:group_id>/leave', methods=['POST'])
@jwt_required()
def leave_group(group_id):
    """離開群組"""
    user_id = int(get_jwt_identity())
    
    member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
    if not member:
        return jsonify({'error': '您不是該群組成員'}), 404
    
    try:
        db.session.delete(member)
        db.session.commit()
        return jsonify({'message': '已離開群組'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/<int:group_id>/members', methods=['GET'])
@jwt_required()
def get_group_members(group_id):
    """取得群組成員清單"""
    from models.user import User
    
    members = db.session.query(User.id, User.name, User.email).join(
        GroupMember, User.id == GroupMember.user_id
    ).filter(GroupMember.group_id == group_id).all()
    
    return jsonify([{
        'user_id': m.id,
        'name': m.name,
        'email': m.email
    } for m in members]), 200

@groups_bp.route('/<int:group_id>/messages', methods=['GET'])
@jwt_required()
def get_group_messages(group_id):
    """取得群組訊息"""
    from models.user import User
    
    messages = db.session.query(
        Message.message_id,
        Message.content,
        Message.created_at,
        User.name.label('sender_name')
    ).join(User, Message.sender_id == User.id).filter(
        Message.group_id == group_id
    ).order_by(Message.created_at).all()
    
    return jsonify([{
        'message_id': m.message_id,
        'content': m.content,
        'sender_name': m.sender_name,
        'created_at': m.created_at.isoformat() if m.created_at else None
    } for m in messages]), 200

@groups_bp.route('/<int:group_id>/messages', methods=['POST'])
@jwt_required()
def send_message(group_id):
    """發送群組訊息"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'error': '訊息內容不可為空'}), 400
    
    # 檢查是否為群組成員
    member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
    if not member:
        return jsonify({'error': '您不是該群組成員'}), 403
    
    new_message = Message(
        group_id=group_id,
        sender_id=user_id,
        content=content
    )
    
    try:
        db.session.add(new_message)
        db.session.commit()
        return jsonify({'message': '訊息已發送', 'message_id': new_message.message_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
