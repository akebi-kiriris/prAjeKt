from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from app import db
from models.user import User

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/me', methods=['GET'])
@jwt_required()
def get_profile():
    """取得使用者個人資料"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '使用者不存在'}), 404
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email,
        'phone': user.phone,
        'created_at': user.created_at.isoformat() if user.created_at else None
    }), 200

@profile_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新使用者個人資料"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '使用者不存在'}), 404
    
    data = request.get_json()
    
    # 更新允許的欄位
    if 'name' in data:
        user.name = data['name']
    if 'username' in data:
        # 檢查 username 是否已被使用
        if data['username'] and User.query.filter(User.username == data['username'], User.id != user_id).first():
            return jsonify({'error': '此用戶名已被使用'}), 409
        user.username = data['username'] if data['username'] else None
    if 'phone' in data:
        user.phone = data['phone']
    if 'email' in data:
        user.email = data['email']
    
    # 處理密碼變更
    if data.get('new_password'):
        if not data.get('current_password'):
            return jsonify({'error': '請提供目前密碼'}), 400
        
        if not check_password_hash(user.password, data['current_password']):
            return jsonify({'error': '目前密碼錯誤'}), 401
        
        user.password = generate_password_hash(data['new_password'])
    
    try:
        db.session.commit()
        return jsonify({'message': '個人資料更新成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/search', methods=['POST'])
@jwt_required()
def search_user():
    """搜尋使用者（透過 username 或 email）"""
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'error': '請提供搜尋條件'}), 400
    
    # 搜尋 username 或 email
    user = User.query.filter(
        (User.username == query) | (User.email == query)
    ).first()
    
    if not user:
        return jsonify({'error': '找不到使用者'}), 404
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email
    }), 200
