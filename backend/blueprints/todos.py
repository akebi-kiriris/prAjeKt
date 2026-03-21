from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.todo import Todo
from datetime import datetime
from services.todo_service import (
    TODO_CREATE_ALLOWED_FIELDS,
    TODO_UPDATE_ALLOWED_FIELDS,
    find_unknown_fields,
    todo_to_dict,
)

todos_bp = Blueprint('todos', __name__)

@todos_bp.route('', methods=['GET'])
@jwt_required()
def get_todos():
    """取得使用者的所有待辦事項"""
    user_id = int(get_jwt_identity())
    todo_id = request.args.get('id')
    
    if todo_id:
        # 取得單一待辦事項（排除軟刪除）
        todo = Todo.query.filter_by(id=todo_id, user_id=user_id).filter(Todo.deleted_at.is_(None)).first()
        if not todo:
            return jsonify({'error': '找不到該待辦事項'}), 404
        return jsonify([todo_to_dict(todo)]), 200
    
    # 取得所有待辦事項（排除軟刪除）
    todos = Todo.query.filter_by(user_id=user_id).filter(Todo.deleted_at.is_(None)).order_by(Todo.completed, Todo.deadline).all()
    
    return jsonify([todo_to_dict(t) for t in todos]), 200

@todos_bp.route('', methods=['POST'])
@jwt_required()
def create_todo():
    """新增待辦事項"""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    if not isinstance(data, dict):
        return jsonify({'error': '請提供正確的 JSON 物件'}), 400

    unknown_fields = find_unknown_fields(data, TODO_CREATE_ALLOWED_FIELDS)
    if unknown_fields:
        return jsonify({'error': f'不允許的欄位: {", ".join(unknown_fields)}'}), 400
    
    content = data.get('content')
    title = data.get('title')
    if not isinstance(content, str):
        return jsonify({'error': '內容必須是字串'}), 400
    if not content or not title :
        return jsonify({'error': '請確認是否有填入事項名稱或內容'}), 400

    priority = data.get('priority', 2)
    try:
        priority = int(priority)
    except (TypeError, ValueError):
        return jsonify({'error': 'priority 必須是數字'}), 400
    if priority < 1 or priority > 3:
        return jsonify({'error': 'priority 必須介於 1 到 3'}), 400

    try:
        deadline = datetime.fromisoformat(data['deadline']) if data.get('deadline') else None
    except ValueError:
        return jsonify({'error': 'deadline 格式錯誤'}), 400
    
    new_todo = Todo(
        user_id=user_id,
        title=data['title'],
        content=data['content'],
        type=data.get('type'),
        deadline=deadline,
        completed=False,
        priority=priority,
    )
    
    try:
        db.session.add(new_todo)
        db.session.commit()
        return jsonify({'message': '待辦事項新增成功', 'id': new_todo.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@todos_bp.route('/<int:todo_id>', methods=['PUT'])
@jwt_required()
def update_todo(todo_id):
    """更新待辦事項"""
    user_id = int(get_jwt_identity())
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).filter(Todo.deleted_at.is_(None)).first()
    
    if not todo:
        return jsonify({'error': '找不到該待辦事項'}), 404
    
    data = request.get_json() or {}

    if not isinstance(data, dict):
        return jsonify({'error': '請提供正確的 JSON 物件'}), 400

    unknown_fields = find_unknown_fields(data, TODO_UPDATE_ALLOWED_FIELDS)
    if unknown_fields:
        return jsonify({'error': f'不允許的欄位: {", ".join(unknown_fields)}'}), 400

    if 'title' in data:
        if not isinstance(data['title'], str) or not data['title'].strip():
            return jsonify({'error': '事項名稱必須是非空字串'}), 400
        todo.title = data['title'].strip()
    
    if 'content' in data:
        if not isinstance(data['content'], str):
            return jsonify({'error': '內容必須是字串'}), 400
        todo.content = data['content']

    if 'type' in data:
        if data['type'] is not None and not isinstance(data['type'], str):
            return jsonify({'error': 'type 必須是字串或 null'}), 400
        todo.type = data['type']
    
    if 'deadline' in data:
        try:
            todo.deadline = datetime.fromisoformat(data['deadline']) if data['deadline'] else None
        except ValueError:
            return jsonify({'error': 'deadline 格式錯誤'}), 400

    if 'priority' in data:
        try:
            priority = int(data['priority'])
        except (TypeError, ValueError):
            return jsonify({'error': 'priority 必須是數字'}), 400
        if priority < 1 or priority > 3:
            return jsonify({'error': 'priority 必須介於 1 到 3'}), 400
        todo.priority = priority

    if 'completed' in data:
        if not isinstance(data['completed'], bool):
            return jsonify({'error': 'completed 必須是布林值'}), 400
        todo.completed = data['completed']
        todo.completed_at = datetime.utcnow() if data['completed'] else None
    
    try:
        db.session.commit()
        return jsonify({'message': '待辦事項更新成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@todos_bp.route('/<int:todo_id>', methods=['DELETE'])
@jwt_required()
def delete_todo(todo_id):
    """刪除待辦事項（軟刪除）"""
    user_id = int(get_jwt_identity())
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).filter(Todo.deleted_at.is_(None)).first()
    
    if not todo:
        return jsonify({'error': '找不到該待辦事項'}), 404
    
    try:
        todo.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': '待辦事項刪除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@todos_bp.route('/<int:todo_id>/toggle', methods=['PATCH'])
@jwt_required()
def toggle_todo(todo_id):
    """切換待辦事項完成狀態"""
    user_id = int(get_jwt_identity())
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).filter(Todo.deleted_at.is_(None)).first()
    
    if not todo:
        return jsonify({'error': '找不到該待辦事項'}), 404
    
    todo.completed = not todo.completed
    todo.completed_at = datetime.utcnow() if todo.completed else None
    
    try:
        db.session.commit()
        return jsonify({'message': '狀態更新成功', 'completed': todo.completed}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
