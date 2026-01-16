from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models.task import Task
from models.task_user import TaskUser
from models.task_comment import TaskComment
from models.user import User
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('', methods=['GET'])
@jwt_required()
def get_tasks():
    """取得使用者的所有任務（包含被指派的）"""
    user_id = int(get_jwt_identity())
    
    # 取得自己建立的任務和被指派的任務
    own_tasks = Task.query.filter_by(user_id=user_id).all()
    assigned_task_ids = [tu.task_id for tu in TaskUser.query.filter_by(user_id=user_id).all()]
    assigned_tasks = Task.query.filter(Task.task_id.in_(assigned_task_ids)).all() if assigned_task_ids else []
    
    # 合併並去重
    all_tasks = {t.task_id: t for t in own_tasks + assigned_tasks}
    tasks = sorted(all_tasks.values(), key=lambda t: (t.completed, t.end_date or datetime.max))
    
    result = []
    for t in tasks:
        # 取得任務成員
        members = TaskUser.query.filter_by(task_id=t.task_id).all()
        member_list = []
        for m in members:
            user = User.query.get(m.user_id)
            if user:
                member_list.append({
                    'user_id': user.id,
                    'name': user.name,
                    'role': m.role  # 0: 負責人, 1: 協作者
                })
        
        result.append({
            'task_id': t.task_id,
            'name': t.name,
            'completed': t.completed,
            'timeline_id': t.timeline_id,
            'assistant': t.assistant,
            'priority': t.priority,
            'status': t.status,
            'tags': t.tags,
            'estimated_hours': t.estimated_hours,
            'actual_hours': t.actual_hours,
            'members': member_list,
            'created_at': t.created_at.isoformat() if t.created_at else None,
            'start_date': t.start_date.isoformat() if t.start_date else None,
            'end_date': t.end_date.isoformat() if t.end_date else None,
            'updated_at': t.updated_at.isoformat() if t.updated_at else None,
            'task_remark': t.task_remark,
            'isWork': t.isWork,
            'is_owner': t.user_id == user_id
        })
    
    return jsonify(result), 200

@tasks_bp.route('', methods=['POST'])
@jwt_required()
def create_task():
    """新增任務"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data.get('name') or not data.get('end_date'):
        return jsonify({'error': '請提供標題和截止日期'}), 400
    
    new_task = Task(
        user_id=user_id,
        name=data['name'],
        timeline_id=data.get('timeline_id'),
        assistant=data.get('assistant'),
        priority=data.get('priority', 2),
        status=data.get('status', 'pending'),
        tags=data.get('tags'),
        estimated_hours=data.get('estimated_hours'),
        start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else None,
        end_date=datetime.fromisoformat(data['end_date']),
        task_remark=data.get('task_remark'),
        isWork=data.get('isWork', 0)
    )
    
    try:
        db.session.add(new_task)
        db.session.flush()  # 取得 task_id
        
        # 自動將建立者加入為負責人
        task_owner = TaskUser(
            task_id=new_task.task_id,
            user_id=user_id,
            role=0  # 負責人
        )
        db.session.add(task_owner)
        
        # 如果有指定成員，加入他們
        if data.get('members'):
            for member in data['members']:
                if member.get('user_id') != user_id:  # 不重複加入建立者
                    task_member = TaskUser(
                        task_id=new_task.task_id,
                        user_id=member['user_id'],
                        role=member.get('role', 1)  # 默認為協作者
                    )
                    db.session.add(task_member)
        
        db.session.commit()
        return jsonify({'message': '任務新增成功', 'task_id': new_task.task_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """更新任務"""
    user_id = int(get_jwt_identity())
    task = Task.query.filter_by(task_id=task_id).first()
    
    if not task:
        return jsonify({'error': '找不到該任務'}), 404
    
    # 檢查是否為任務擁有者或成員
    is_member = TaskUser.query.filter_by(task_id=task_id, user_id=user_id).first()
    if task.user_id != user_id and not is_member:
        return jsonify({'error': '無權限修改此任務'}), 403
    
    data = request.get_json()
    
    task.name = data.get('name', task.name)
    task.timeline_id = data.get('timeline_id', task.timeline_id)
    task.assistant = data.get('assistant', task.assistant)
    task.priority = data.get('priority', task.priority)
    task.status = data.get('status', task.status)
    task.tags = data.get('tags', task.tags)
    task.estimated_hours = data.get('estimated_hours', task.estimated_hours)
    task.actual_hours = data.get('actual_hours', task.actual_hours)
    task.task_remark = data.get('task_remark', task.task_remark)
    task.isWork = data.get('isWork', task.isWork)
    
    if data.get('start_date'):
        task.start_date = datetime.fromisoformat(data['start_date'])
    if data.get('end_date'):
        task.end_date = datetime.fromisoformat(data['end_date'])
    
    try:
        db.session.commit()
        return jsonify({'message': '任務更新成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """刪除任務"""
    user_id = int(get_jwt_identity())
    task = Task.query.filter_by(task_id=task_id, user_id=user_id).first()
    
    if not task:
        return jsonify({'error': '找不到該任務或無權限刪除'}), 404
    
    try:
        # 刪除相關的任務成員
        TaskUser.query.filter_by(task_id=task_id).delete()
        # 刪除相關的任務留言
        TaskComment.query.filter_by(task_id=task_id).delete()
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': '任務刪除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>/toggle', methods=['PATCH'])
@jwt_required()
def toggle_task(task_id):
    """切換任務完成狀態"""
    user_id = int(get_jwt_identity())
    task = Task.query.filter_by(task_id=task_id).first()
    
    if not task:
        return jsonify({'error': '找不到該任務'}), 404
    
    # 檢查是否為任務擁有者或成員
    is_member = TaskUser.query.filter_by(task_id=task_id, user_id=user_id).first()
    if task.user_id != user_id and not is_member:
        return jsonify({'error': '無權限修改此任務'}), 403
    
    task.completed = not task.completed
    task.status = 'completed' if task.completed else 'pending'
    
    try:
        db.session.commit()
        return jsonify({'message': '狀態更新成功', 'completed': task.completed}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===== 任務成員 API =====

@tasks_bp.route('/<int:task_id>/members', methods=['GET'])
@jwt_required()
def get_task_members(task_id):
    """取得任務成員列表"""
    members = TaskUser.query.filter_by(task_id=task_id).all()
    result = []
    for m in members:
        user = User.query.get(m.user_id)
        if user:
            result.append({
                'user_id': user.id,
                'name': user.name,
                'email': user.email,
                'avatar': user.avatar,
                'role': m.role,
                'assigned_at': m.assigned_at.isoformat() if m.assigned_at else None
            })
    return jsonify(result), 200

@tasks_bp.route('/<int:task_id>/members', methods=['POST'])
@jwt_required()
def add_task_member(task_id):
    """新增任務成員"""
    user_id = int(get_jwt_identity())
    task = Task.query.filter_by(task_id=task_id).first()
    
    if not task:
        return jsonify({'error': '找不到該任務'}), 404
    
    if task.user_id != user_id:
        return jsonify({'error': '只有任務建立者可以新增成員'}), 403
    
    data = request.get_json()
    new_user_id = data.get('user_id')
    
    if not new_user_id:
        return jsonify({'error': '請提供使用者 ID'}), 400
    
    # 檢查是否已是成員
    existing = TaskUser.query.filter_by(task_id=task_id, user_id=new_user_id).first()
    if existing:
        return jsonify({'error': '該使用者已是任務成員'}), 409
    
    try:
        task_member = TaskUser(
            task_id=task_id,
            user_id=new_user_id,
            role=data.get('role', 1)
        )
        db.session.add(task_member)
        db.session.commit()
        return jsonify({'message': '成員新增成功'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>/members/<int:member_id>', methods=['DELETE'])
@jwt_required()
def remove_task_member(task_id, member_id):
    """移除任務成員"""
    user_id = int(get_jwt_identity())
    task = Task.query.filter_by(task_id=task_id).first()
    
    if not task:
        return jsonify({'error': '找不到該任務'}), 404
    
    if task.user_id != user_id:
        return jsonify({'error': '只有任務建立者可以移除成員'}), 403
    
    if member_id == task.user_id:
        return jsonify({'error': '無法移除任務建立者'}), 400
    
    try:
        TaskUser.query.filter_by(task_id=task_id, user_id=member_id).delete()
        db.session.commit()
        return jsonify({'message': '成員移除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===== 任務留言 API =====

@tasks_bp.route('/<int:task_id>/comments', methods=['GET'])
@jwt_required()
def get_task_comments(task_id):
    """取得任務留言"""
    comments = TaskComment.query.filter_by(task_id=task_id).order_by(TaskComment.created_at.desc()).all()
    result = []
    for c in comments:
        user = User.query.get(c.user_id)
        result.append({
            'comment_id': c.comment_id,
            'user_id': c.user_id,
            'user_name': user.name if user else '未知使用者',
            'user_avatar': user.avatar if user else None,
            'task_message': c.task_message,
            'created_at': c.created_at.isoformat() if c.created_at else None
        })
    return jsonify(result), 200

@tasks_bp.route('/<int:task_id>/comments', methods=['POST'])
@jwt_required()
def add_task_comment(task_id):
    """新增任務留言"""
    user_id = int(get_jwt_identity())
    task = Task.query.filter_by(task_id=task_id).first()
    
    if not task:
        return jsonify({'error': '找不到該任務'}), 404
    
    data = request.get_json()
    message = data.get('message') or data.get('task_message')
    
    if not message:
        return jsonify({'error': '請提供留言內容'}), 400
    
    try:
        comment = TaskComment(
            task_id=task_id,
            user_id=user_id,
            task_message=message
        )
        db.session.add(comment)
        db.session.commit()
        return jsonify({'message': '留言新增成功', 'comment_id': comment.comment_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_task_comment(task_id, comment_id):
    """刪除任務留言"""
    user_id = int(get_jwt_identity())
    comment = TaskComment.query.filter_by(comment_id=comment_id, task_id=task_id).first()
    
    if not comment:
        return jsonify({'error': '找不到該留言'}), 404
    
    if comment.user_id != user_id:
        return jsonify({'error': '只能刪除自己的留言'}), 403
    
    try:
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'message': '留言刪除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
