from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from services.auth_service import (
    AuthOperationError,
    auth_user_to_dict,
    authenticate_user,
    current_user_to_dict,
    get_current_user_or_404,
    register_user,
)

auth_bp = Blueprint('auth', __name__)


def _get_json_dict_or_400():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({'error': '請提供正確的 JSON 物件'}), 400)
    return data, None

@auth_bp.route('/register', methods=['POST'])
def register():
    """註冊新使用者"""
    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        user_id = register_user(data)
        return jsonify({'message': '註冊成功', 'user_id': user_id}), 201
    except AuthOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@auth_bp.route('/login', methods=['POST'])
def login():
    """使用者登入"""
    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        user = authenticate_user(data.get('email'), data.get('password'))
    except AuthOperationError as err:
        return jsonify({'error': err.message}), err.status_code
    
    # 建立 JWT tokens
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': auth_user_to_dict(user)
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

    try:
        user = get_current_user_or_404(user_id)
        return jsonify(current_user_to_dict(user)), 200
    except AuthOperationError as err:
        return jsonify({'error': err.message}), err.status_code
    
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
