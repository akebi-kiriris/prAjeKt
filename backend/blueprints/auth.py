from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app import db
from models.user import User
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """註冊新使用者"""
    data = request.get_json()
    
    name = data.get('name')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    
    if not all([name, email, password]):
        return jsonify({'error': '缺少必要欄位'}), 400
    
    # 檢查 email 是否已存在
    if User.query.filter_by(email=email).first():
        return jsonify({'error': '此 email 已被註冊'}), 409
    
    # 檢查 username 是否已存在（如果提供）
    if username and User.query.filter_by(username=username).first():
        return jsonify({'error': '此用戶名已被使用'}), 409
    
    # 建立新使用者
    hashed_password = generate_password_hash(password)
    new_user = User(
        name=name,
        username=username if username else None,
        email=email,
        password=hashed_password,
        phone=phone
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': '註冊成功', 'user_id': new_user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """使用者登入"""
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': '請提供 email 和密碼'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not check_password_hash(user.password, password):
        return jsonify({'error': '帳號或密碼錯誤'}), 401
    
    # 建立 JWT tokens
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user.id,
            'name': user.name,
            'username': user.username,
            'email': user.email
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """登出"""
    # JWT 無狀態，前端刪除 token 即可
    return jsonify({'message': '登出成功'}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """取得當前使用者資訊"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '使用者不存在'}), 404
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email,
        'phone': user.phone
    }), 200
    
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_access_token():
    """使用 refresh token 取得新的 access token"""
    # 從 refresh token 中取得 user_id
    user_id = get_jwt_identity()
    
    # 產生新的 access token
    new_access_token = create_access_token(identity=user_id)
    
    return jsonify({
        'access_token': new_access_token
    }), 200
