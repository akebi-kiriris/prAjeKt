from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.todo_service import (
    TodoOperationError,
    create_todo_for_user,
    list_todos_for_user,
    soft_delete_todo_for_user,
    todo_to_dict,
    toggle_todo_for_user,
    update_todo_for_user,
)

todos_bp = Blueprint('todos', __name__)


def _get_json_dict_or_400():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({'error': '請提供正確的 JSON 物件'}), 400)
    return data, None

@todos_bp.route('', methods=['GET'])
@jwt_required()
def get_todos():
    """取得使用者的所有待辦事項"""
    user_id = int(get_jwt_identity())
    todo_id = request.args.get('id')

    try:
        todos = list_todos_for_user(user_id, todo_id=todo_id)
        return jsonify([todo_to_dict(t) for t in todos]), 200
    except TodoOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@todos_bp.route('', methods=['POST'])
@jwt_required()
def create_todo():
    """新增待辦事項"""
    user_id = int(get_jwt_identity())
    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        todo_id = create_todo_for_user(user_id, data)
        return jsonify({'message': '待辦事項新增成功', 'id': todo_id}), 201
    except TodoOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@todos_bp.route('/<int:todo_id>', methods=['PUT'])
@jwt_required()
def update_todo(todo_id):
    """更新待辦事項"""
    user_id = int(get_jwt_identity())
    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        update_todo_for_user(todo_id, user_id, data)
        return jsonify({'message': '待辦事項更新成功'}), 200
    except TodoOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@todos_bp.route('/<int:todo_id>', methods=['DELETE'])
@jwt_required()
def delete_todo(todo_id):
    """刪除待辦事項（軟刪除）"""
    user_id = int(get_jwt_identity())

    try:
        soft_delete_todo_for_user(todo_id, user_id)
        return jsonify({'message': '待辦事項刪除成功'}), 200
    except TodoOperationError as err:
        return jsonify({'error': err.message}), err.status_code

@todos_bp.route('/<int:todo_id>/toggle', methods=['PATCH'])
@jwt_required()
def toggle_todo(todo_id):
    """切換待辦事項完成狀態"""
    user_id = int(get_jwt_identity())

    try:
        completed = toggle_todo_for_user(todo_id, user_id)
        return jsonify({'message': '狀態更新成功', 'completed': completed}), 200
    except TodoOperationError as err:
        return jsonify({'error': err.message}), err.status_code
