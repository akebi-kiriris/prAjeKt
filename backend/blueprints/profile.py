from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.profile_service import (
    ProfileOperationError,
    build_chart_stats_for_user,
    get_profile_user_or_404,
    profile_to_dict,
    search_user_by_query,
    search_user_to_dict,
    update_profile_for_user,
)

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/me', methods=['GET'])
@jwt_required()
def get_profile():
    """取得使用者個人資料"""
    user_id = int(get_jwt_identity())

    try:
        user = get_profile_user_or_404(user_id)
        return jsonify(profile_to_dict(user)), 200
    except ProfileOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@profile_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新使用者個人資料"""
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)

    try:
        update_profile_for_user(user_id, data)
        return jsonify({'message': '個人資料更新成功'}), 200
    except ProfileOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@profile_bp.route('/search', methods=['POST'])
@jwt_required()
def search_user():
    """搜尋使用者（透過 username 或 email）"""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': '請提供正確的 JSON 物件'}), 400

    try:
        user = search_user_by_query(data.get('query', ''))
        return jsonify(search_user_to_dict(user)), 200
    except ProfileOperationError as err:
        return jsonify({'error': err.message}), err.status_code


@profile_bp.route('/chart-stats', methods=['GET'])
@jwt_required()
def get_chart_stats():
    """取得個人數據分析圖表資料"""
    user_id = int(get_jwt_identity())
    return jsonify(build_chart_stats_for_user(user_id)), 200
