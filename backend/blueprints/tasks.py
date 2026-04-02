from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.task_service import (
    TaskOperationError,
    add_task_comment_for_member,
    add_task_member_for_operator,
    create_task_for_user,
    create_subtask_for_task,
    delete_task_file_for_user,
    delete_subtask_for_task,
    get_task_members_with_contact,
    list_subtasks_for_task,
    list_task_files_for_member,
    list_task_comments_for_member,
    list_tasks_for_user,
    list_upcoming_tasks_for_user,
    remove_task_member_for_owner,
    require_task_role,
    resolve_task_file_download_for_user,
    summarize_task_comments_for_member,
    soft_delete_task_comment_for_user,
    soft_delete_task_for_owner,
    toggle_task_for_member,
    toggle_subtask_for_task,
    upload_task_file_for_member,
    update_subtask_for_task,
    update_task_member_role_for_operator,
    update_task_status_for_member,
    update_task_for_member,
)

tasks_bp = Blueprint('tasks', __name__)


def _get_json_dict_or_400():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({'error': '請提供正確的 JSON 物件'}), 400)
    return data, None

@tasks_bp.route('', methods=['GET'])
@jwt_required()
def get_tasks():
    """取得使用者的所有任務（包含被指派的）"""
    user_id = int(get_jwt_identity())

    return jsonify(list_tasks_for_user(user_id)), 200

@tasks_bp.route('', methods=['POST'])
@jwt_required()
def create_task():
    """新增任務"""
    user_id = int(get_jwt_identity())
    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        task_id = create_task_for_user(user_id, data)
        return jsonify({'message': '任務新增成功', 'task_id': task_id}), 201
    except TaskOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
@require_task_role('member')
def update_task(task_id):
    """更新任務"""
    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        update_task_for_member(task_id, data)
        return jsonify({'message': '任務更新成功'}), 200
    except TaskOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
@require_task_role('owner')
def delete_task(task_id):
    """刪除任務（軟刪除）"""
    try:
        soft_delete_task_for_owner(task_id)
        return jsonify({'message': '任務刪除成功'}), 200
    except TaskOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@tasks_bp.route('/<int:task_id>/toggle', methods=['PATCH'])
@jwt_required()
@require_task_role('member')
def toggle_task(task_id):
    """切換任務完成狀態"""

    try:
        completed = toggle_task_for_member(task_id)
        return jsonify({'message': '狀態更新成功', 'completed': completed}), 200
    except TaskOperationError as err:
        return jsonify({'error': err.message}), err.status_code

# ===== 任務成員 API =====

@tasks_bp.route('/<int:task_id>/members', methods=['GET'])
@jwt_required()
@require_task_role('member')
def get_task_members(task_id):
    """取得任務成員列表"""
    return jsonify(get_task_members_with_contact(task_id)), 200

@tasks_bp.route('/<int:task_id>/members', methods=['POST'])
@jwt_required()
def add_task_member(task_id):
    """新增任務成員（任務負責人 或 所屬 timeline 的負責人 可操作）"""
    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        add_task_member_for_operator(
            task_id=task_id,
            operator_user_id=int(get_jwt_identity()),
            new_user_id=data.get('user_id'),
            role=data.get('role', 1),
        )
        return jsonify({'message': '成員新增成功'}), 201
    except TaskOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@tasks_bp.route('/<int:task_id>/members/<int:member_id>', methods=['DELETE'])
@jwt_required()
@require_task_role('owner')
def remove_task_member(task_id, member_id):
    """移除任務成員"""

    try:
        remove_task_member_for_owner(task_id, member_id)
        return jsonify({'message': '成員移除成功'}), 200
    except TaskOperationError as err:
        return jsonify({'error': err.message}), err.status_code


@tasks_bp.route('/<int:task_id>/members/<int:member_id>', methods=['PATCH'])
@jwt_required()
def update_task_member_role(task_id, member_id):
    """更新任務成員角色。
    當 role=0 時，會把該任務其餘成員降為協作者，形成單一主責人。"""
    payload, error = _get_json_dict_or_400()
    if error:
        return error

    if 'role' not in payload:
        return jsonify({'error': '請提供 role 欄位'}), 400

    try:
        new_role = int(payload.get('role'))
    except (TypeError, ValueError):
        return jsonify({'error': 'role 必須是數字'}), 400

    if new_role not in (0, 1):
        return jsonify({'error': 'role 只允許 0(負責人) 或 1(協作者)'}), 400

    try:
        update_task_member_role_for_operator(
            task_id=task_id,
            member_id=member_id,
            new_role=new_role,
            operator_user_id=int(get_jwt_identity()),
        )
        return jsonify({'message': '成員角色更新成功'}), 200
    except TaskOperationError as err:
        return jsonify({'error': err.message}), err.status_code

# ===== 任務留言 API =====

@tasks_bp.route('/<int:task_id>/comments', methods=['GET'])
@jwt_required()
@require_task_role('member')
def get_task_comments(task_id):
    """取得任務留言"""
    return jsonify(list_task_comments_for_member(task_id)), 200


@tasks_bp.route('/<int:task_id>/ai-comment-summary', methods=['POST'])
@jwt_required()
@require_task_role('member')
def summarize_task_comments(task_id):
    """任務留言 AI 智能摘要（決議 / 風險 / 下一步）"""
    try:
        return jsonify(summarize_task_comments_for_member(task_id)), 200
    except TaskOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@tasks_bp.route('/<int:task_id>/comments', methods=['POST'])
@jwt_required()
@require_task_role('member')
def add_task_comment(task_id):
    """新增任務留言"""
    user_id = int(get_jwt_identity())
    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        payload = add_task_comment_for_member(task_id, user_id, data)
        return jsonify(payload), 201
    except TaskOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@tasks_bp.route('/<int:task_id>/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_task_comment(task_id, comment_id):
    """刪除任務留言（軟刪除）"""

    try:
        soft_delete_task_comment_for_user(task_id, comment_id, int(get_jwt_identity()))
        return jsonify({'message': '留言刪除成功'}), 200
    except TaskOperationError as err:
        return jsonify({'error': err.message}), err.status_code


# ===== 任務檔案 API =====

@tasks_bp.route('/<int:task_id>/files', methods=['GET'])
@jwt_required()
@require_task_role('member')
def get_task_files(task_id):
    """取得任務所有附件"""
    return jsonify(list_task_files_for_member(task_id)), 200

@tasks_bp.route('/<int:task_id>/upload', methods=['POST'])
@jwt_required()
@require_task_role('member')
def upload_task_file(task_id):
    """上傳任務附件"""
    user_id = int(get_jwt_identity())

    if 'file' not in request.files:
        return jsonify({'error': '沒有選擇檔案'}), 400
    file = request.files['file']

    try:
        payload = upload_task_file_for_member(task_id, user_id, file)
        return jsonify(payload), 201
    except TaskOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@tasks_bp.route('/<int:task_id>/files/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_task_file(task_id, file_id):
    """刪除任務附件（上傳者或負責人可刪除）"""
    try:
        delete_task_file_for_user(task_id, file_id, int(get_jwt_identity()))
        return jsonify({'message': '檔案刪除成功'}), 200
    except TaskOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@tasks_bp.route('/files/<filename>', methods=['GET'])
@jwt_required()
def download_task_file(filename):
    """下載/預覽任務附件（以原始檔名呈現）"""

    try:
        upload_folder, safe_name, original_name = resolve_task_file_download_for_user(
            filename,
            int(get_jwt_identity()),
        )
        return send_from_directory(upload_folder, safe_name, as_attachment=False, download_name=original_name)
    except TaskOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@tasks_bp.route('/<int:task_id>/subtasks', methods=['GET'])
@jwt_required()
@require_task_role('member')
def get_subtasks(task_id):
    """取得任務的所有子任務"""
    return jsonify(list_subtasks_for_task(task_id)), 200

@tasks_bp.route('/<int:task_id>/subtasks', methods=['POST'])
@jwt_required()
@require_task_role('member')
def create_subtask(task_id):
    """新增子任務"""
    data, error = _get_json_dict_or_400()
    if error:
        return error


    try:
        subtask = create_subtask_for_task(task_id, data.get('name'))
        return jsonify({'message': '子任務新增成功', 'subtask': subtask}), 201
    except TaskOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@tasks_bp.route('/<int:task_id>/subtasks/<int:subtask_id>', methods=['PUT'])
@jwt_required()
@require_task_role('member')
def update_subtask(task_id, subtask_id):
    """更新子任務"""

    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        subtask = update_subtask_for_task(task_id, subtask_id, data)
        return jsonify({'message': '子任務更新成功', 'subtask': subtask}), 200
    except TaskOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@tasks_bp.route('/<int:task_id>/subtasks/<int:subtask_id>', methods=['DELETE'])
@jwt_required()
@require_task_role('member')
def delete_subtask(task_id, subtask_id):
    """刪除子任務"""

    try:
        delete_subtask_for_task(task_id, subtask_id)
        return jsonify({'message': '子任務刪除成功'}), 200
    except TaskOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@tasks_bp.route('/<int:task_id>/subtasks/<int:subtask_id>/toggle', methods=['PATCH'])
@jwt_required()
@require_task_role('member')
def toggle_subtask(task_id, subtask_id):
    """切換子任務完成狀態"""

    try:
        subtask = toggle_subtask_for_task(task_id, subtask_id)
        return jsonify({'message': '狀態更新成功', 'subtask': subtask}), 200
    except TaskOperationError as err:
        return jsonify({'error': err.message}), err.status_code


# ===== 任務狀態更新 API (看板用) =====

@tasks_bp.route('/<int:task_id>/status', methods=['PATCH'])
@jwt_required()
@require_task_role('member')
def update_task_status(task_id):
    """更新任務狀態（看板拖曳用）"""

    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        status_payload = update_task_status_for_member(task_id, data.get('status'))
        return jsonify({'message': '狀態更新成功', **status_payload}), 200
    except TaskOperationError as err:
        return jsonify({'error': err.message}), err.status_code


@tasks_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_tasks():
    """取得即將到期（3天內）或時間進度超過80%的任務"""
    user_id = int(get_jwt_identity())
    return jsonify(list_upcoming_tasks_for_user(user_id)), 200
