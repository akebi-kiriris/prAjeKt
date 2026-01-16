from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models.todo import Todo
from datetime import datetime

todos_bp = Blueprint('todos', __name__)

@todos_bp.route('', methods=['GET'])
@jwt_required()
def get_todos():
    """取得使用者的所有待辦事項"""
    user_id = int(get_jwt_identity())
    todo_id = request.args.get('id')
    
    if todo_id:
        # 取得單一待辦事項
        todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
        if not todo:
            return jsonify({'error': '找不到該待辦事項'}), 404
        return jsonify([{
            'id': todo.id,
            'title': todo.title,
            'content': todo.content,
            'deadline': todo.deadline.isoformat() if todo.deadline else None,
            'completed': todo.completed
        }]), 200
    
    # 取得所有待辦事項
    todos = Todo.query.filter_by(user_id=user_id).order_by(Todo.completed, Todo.deadline).all()
    
    return jsonify([{
        'id': t.id,
        'title':t.title,
        'content': t.content,
        'deadline': t.deadline.isoformat() if t.deadline else None,
        'completed': t.completed
    } for t in todos]), 200

@todos_bp.route('', methods=['POST'])
@jwt_required()
def create_todo():
    """新增待辦事項"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    content = data.get('content')
    title = data.get('title')
    if not isinstance(content, str):
        return jsonify({'error': '內容必須是字串'}), 400
    if not content or not title :
        return jsonify({'error': '請確認是否有填入事項名稱或內容'}), 400
    
    new_todo = Todo(
        user_id=user_id,
        title=data['title'],
        content=data['content'],
        deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else None,
        completed=False
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
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    
    if not todo:
        return jsonify({'error': '找不到該待辦事項'}), 404
    
    data = request.get_json()
    
    if 'content' in data:
        if not isinstance(data['content'], str):
            return jsonify({'error': '內容必須是字串'}), 400
        todo.content = data['content']
    
    if 'deadline' in data:
        todo.deadline = datetime.fromisoformat(data['deadline']) if data['deadline'] else None
    
    try:
        db.session.commit()
        return jsonify({'message': '待辦事項更新成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@todos_bp.route('/<int:todo_id>', methods=['DELETE'])
@jwt_required()
def delete_todo(todo_id):
    """刪除待辦事項"""
    user_id = int(get_jwt_identity())
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    
    if not todo:
        return jsonify({'error': '找不到該待辦事項'}), 404
    
    try:
        db.session.delete(todo)
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
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    
    if not todo:
        return jsonify({'error': '找不到該待辦事項'}), 404
    
    todo.completed = not todo.completed
    
    try:
        db.session.commit()
        return jsonify({'message': '狀態更新成功', 'completed': todo.completed}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
