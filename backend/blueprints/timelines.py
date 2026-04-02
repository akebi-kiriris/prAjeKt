from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.timeline_service import (
    TimelineOperationError,
    TimelineAIGenerationError,
    add_timeline_member_for_owner,
    batch_create_tasks_for_timeline,
    build_timeline_member_stats_payload,
    create_timeline_for_user,
    generate_timeline_tasks_with_ai,
    get_active_timeline_or_404,
    list_timeline_items_for_user,
    list_timeline_members_payload,
    list_timeline_tasks_detail,
    list_upcoming_timelines_for_user,
    remove_timeline_member_for_owner,
    require_timeline_role,
    search_timeline_user_by_email,
    soft_delete_timeline_for_owner,
    update_timeline_for_member,
    update_timeline_remark_for_member,
)

timelines_bp = Blueprint('timelines', __name__)


def _get_json_dict_or_400():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({'error': '請提供正確的 JSON 物件'}), 400)
    return data, None

@timelines_bp.route('', methods=['GET'])
@jwt_required()
def get_timelines():
    """取得使用者的所有專案時程（包含被邀請的）"""
    user_id = int(get_jwt_identity())
    return jsonify(list_timeline_items_for_user(user_id)), 200


@timelines_bp.route('', methods=['POST'])
@jwt_required()
def create_timeline():
    """新增專案時程"""
    user_id = int(get_jwt_identity())
    data, error = _get_json_dict_or_400()
    if error:
        return error
    
    try:
        timeline_id = create_timeline_for_user(user_id, data)
        return jsonify({'message': '專案新增成功', 'id': timeline_id}), 201
    except TimelineOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@timelines_bp.route('/<int:timeline_id>', methods=['PUT'])
@jwt_required()
@require_timeline_role('member')
def update_timeline(timeline_id):
    """更新專案時程（負責人或協作者均可）"""
    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        update_timeline_for_member(timeline_id, data)
        return jsonify({'message': '專案更新成功'}), 200
    except TimelineOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@timelines_bp.route('/<int:timeline_id>', methods=['DELETE'])
@jwt_required()
@require_timeline_role('owner')
def delete_timeline(timeline_id):
    """刪除專案時程（軟刪除，僅負責人可操作）"""
    try:
        soft_delete_timeline_for_owner(timeline_id)
        return jsonify({'message': '專案刪除成功'}), 200
    except TimelineOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@timelines_bp.route('/<int:timeline_id>/tasks', methods=['GET'])
@jwt_required()
@require_timeline_role('member')
def get_timeline_tasks(timeline_id):
    """取得專案的所有任務（含負責人、助理資訊）"""
    return jsonify(list_timeline_tasks_detail(timeline_id)), 200

@timelines_bp.route('/<int:timeline_id>/remark', methods=['PUT'])
@jwt_required()
@require_timeline_role('member')
def update_timeline_remark(timeline_id):
    """修改專案備註（負責人或協作者均可）"""
    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        update_timeline_remark_for_member(timeline_id, data.get('remark', ''))
        return jsonify({'message': '備註更新成功'}), 200
    except TimelineOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@timelines_bp.route('/search_user', methods=['POST'])
@jwt_required()
def search_user_by_email():
    """根據 Email 搜尋使用者"""
    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        user = search_timeline_user_by_email(data.get('email'))
        return jsonify({
            'id': user.id,
            'name': user.name,
            'email': user.email,
        }), 200
    except TimelineOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@timelines_bp.route('/<int:timeline_id>/members', methods=['GET'])
@jwt_required()
@require_timeline_role('member')
def get_timeline_members(timeline_id):
    """取得專案成員列表（成員皆可查）"""
    return jsonify(list_timeline_members_payload(timeline_id)), 200


@timelines_bp.route('/<int:timeline_id>/members', methods=['POST'])
@jwt_required()
@require_timeline_role('owner')
def add_timeline_member(timeline_id):
    """邀請人員加入專案（僅負責人可操作）"""
    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        add_timeline_member_for_owner(
            timeline_id=timeline_id,
            invited_user_id=data.get('user_id'),
            role=data.get('role', 1),
            actor_user_id=int(get_jwt_identity()),
        )
        return jsonify({'message': '成員新增成功'}), 201
    except TimelineOperationError as err:
        return jsonify({'error': err.message}), err.status_code


@timelines_bp.route('/<int:timeline_id>/members/<int:member_user_id>', methods=['DELETE'])
@jwt_required()
@require_timeline_role('owner')
def remove_timeline_member(timeline_id, member_user_id):
    """將成員移出專案（僅負責人可操作，且不能移除自己）"""
    user_id = int(get_jwt_identity())

    try:
        remove_timeline_member_for_owner(timeline_id, member_user_id, user_id)
        return jsonify({'message': '成員已移除'}), 200
    except TimelineOperationError as err:
        return jsonify({'error': err.message}), err.status_code


# ===== AI 任務生成 API =====

@timelines_bp.route('/<int:timeline_id>/generate-tasks', methods=['POST'])
@jwt_required()
@require_timeline_role('member')
def generate_tasks_with_ai(timeline_id):
    """使用 AI 自動生成任務清單（負責人或協作者均可）"""
    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        timeline = get_active_timeline_or_404(timeline_id)
    except TimelineOperationError as err:
        return jsonify({'error': err.message}), err.status_code

    project_name = data.get('name', timeline.name)
    description = data.get('description', timeline.remark or '')
    
    if not project_name.strip():
        return jsonify({'error': '請提供專案名稱'}), 400

    try:
        result = generate_timeline_tasks_with_ai(
            timeline_id=timeline_id,
            project_name=project_name,
            description=description,
        )
        return jsonify(result), 200
    except TimelineAIGenerationError as err:
        if err.code == 'missing_api_key':
            return jsonify({'error': err.message}), 500
        if err.code == 'json_decode_error':
            return jsonify({'error': 'AI 回應解析失敗'}), 500
        if err.code == 'invalid_payload':
            return jsonify({'error': 'AI 回傳格式錯誤'}), 500
        return jsonify({'error': 'AI 生成失敗，請稍後再試'}), 500


@timelines_bp.route('/<int:timeline_id>/batch-create-tasks', methods=['POST'])
@jwt_required()
@require_timeline_role('member')
def batch_create_tasks(timeline_id):
    """批量創建任務（用於 AI 生成後確認）"""
    user_id = int(get_jwt_identity())
    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        payload = batch_create_tasks_for_timeline(timeline_id, user_id, data.get('tasks', []))
        return jsonify(payload), 201
    except TimelineOperationError as err:
        return jsonify({'error': err.message}), err.status_code


@timelines_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_timelines():
    """取得即將到期（3天內）或時間進度超過80%的專案"""
    user_id = int(get_jwt_identity())
    return jsonify(list_upcoming_timelines_for_user(user_id)), 200


@timelines_bp.route('/<int:timeline_id>/member-stats', methods=['GET'])
@jwt_required()
@require_timeline_role('owner')
def get_member_stats(timeline_id):
    """取得專案成員任務統計（負責人限定）"""
    return jsonify(build_timeline_member_stats_payload(timeline_id)), 200
