from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from sqlalchemy import text
from app import db
from models.timeline import Timeline, TaskFile
from models.task import Task
from models.user import User
from datetime import datetime
import os

timelines_bp = Blueprint('timelines', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@timelines_bp.route('', methods=['GET'])
@jwt_required()
def get_timelines():
    """取得使用者的所有專案時程"""
    user_id = int(get_jwt_identity())
    timelines = Timeline.query.filter_by(user_id=user_id).all()
    
    result = []
    for timeline in timelines:
        # 計算任務統計
        tasks = Task.query.filter_by(timeline_id=timeline.id, user_id=user_id).all()
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.completed])
        
        result.append({
            'id': timeline.id,
            'name': timeline.name,
            'startDate': timeline.start_date.isoformat() if timeline.start_date else None,
            'endDate': timeline.end_date.isoformat() if timeline.end_date else None,
            'remark': timeline.remark,
            'totalTasks': total_tasks,
            'completedTasks': completed_tasks
        })
    
    return jsonify(result), 200

@timelines_bp.route('', methods=['POST'])
@jwt_required()
def create_timeline():
    """新增專案時程"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    name = data.get('name')
    start_date_raw = data.get('start_date', '')
    end_date_raw = data.get('end_date', '')
    remark = data.get('remark', '')

    if not isinstance(name, str) or not name.strip():
        return jsonify({'error': '請提供專案名稱（字串）'}), 400
    if not isinstance(start_date_raw, str):
        return jsonify({'error': '開始日期必須是字串'}), 400
    if not isinstance(end_date_raw, str):
        return jsonify({'error': '結束日期必須是字串'}), 400

    # 解析日期，允許空字串
    start_date = None
    if start_date_raw.strip():
        try:
            start_date = datetime.fromisoformat(start_date_raw)
        except ValueError:
            return jsonify({'error': '開始日期格式錯誤，請用 YYYY-MM-DD'}), 400

    end_date = None
    if end_date_raw.strip():
        try:
            end_date = datetime.fromisoformat(end_date_raw)
        except ValueError:
            return jsonify({'error': '結束日期格式錯誤，請用 YYYY-MM-DD'}), 400

    new_timeline = Timeline(
        user_id=user_id,
        name=name.strip(),
        start_date=start_date,
        end_date=end_date,
        remark=remark
    )
    
    try:
        db.session.add(new_timeline)
        db.session.commit()
        return jsonify({'message': '專案新增成功', 'id': new_timeline.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@timelines_bp.route('/<int:timeline_id>', methods=['PUT'])
@jwt_required()
def update_timeline(timeline_id):
    """更新專案時程"""
    user_id = int(get_jwt_identity())
    timeline = Timeline.query.filter_by(id=timeline_id, user_id=user_id).first()
    
    if not timeline:
        return jsonify({'error': '找不到該專案'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        if not data['name'] or not data['name'].strip():
            return jsonify({'error': '專案名稱不可為空'}), 400
        timeline.name = data['name'].strip()
    
    if 'start_date' in data:
        if data['start_date'] and data['start_date'].strip():
            try:
                timeline.start_date = datetime.fromisoformat(data['start_date'])
            except ValueError:
                return jsonify({'error': '開始日期格式錯誤'}), 400
        else:
            timeline.start_date = None
    
    if 'end_date' in data:
        if data['end_date'] and data['end_date'].strip():
            try:
                timeline.end_date = datetime.fromisoformat(data['end_date'])
            except ValueError:
                return jsonify({'error': '結束日期格式錯誤'}), 400
        else:
            timeline.end_date = None
    
    if 'remark' in data:
        timeline.remark = data['remark']
    
    try:
        db.session.commit()
        return jsonify({'message': '專案更新成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@timelines_bp.route('/<int:timeline_id>', methods=['DELETE'])
@jwt_required()
def delete_timeline(timeline_id):
    """刪除專案時程"""
    user_id = int(get_jwt_identity())
    timeline = Timeline.query.filter_by(id=timeline_id, user_id=user_id).first()
    
    if not timeline:
        return jsonify({'error': '找不到該專案'}), 404
    
    try:
        db.session.delete(timeline)
        db.session.commit()
        return jsonify({'message': '專案刪除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@timelines_bp.route('/<int:timeline_id>/tasks', methods=['GET'])
@jwt_required()
def get_timeline_tasks(timeline_id):
    """取得專案的所有任務（含負責人、助理資訊）"""
    user_id = int(get_jwt_identity())
    tasks = Task.query.filter_by(timeline_id=timeline_id).order_by(Task.end_date).all()
    
    tasks_response = []
    for task in tasks:
        # 從 task_users 表獲取負責人（role=0）
        assignee_query = db.session.execute(
            text("""
                SELECT u.name, u.id
                FROM task_users tu
                JOIN users u ON tu.user_id = u.id
                WHERE tu.task_id = :task_id AND tu.role = 0
                LIMIT 1
            """),
            {'task_id': task.task_id}
        ).fetchone()
        assignee_name = assignee_query[0] if assignee_query else None
        
        # 從 task_users 表獲取助理（role=1）
        assistants_query = db.session.execute(
            text("""
                SELECT u.id, u.name 
                FROM task_users tu
                JOIN users u ON tu.user_id = u.id
                WHERE tu.task_id = :task_id AND tu.role = 1
            """),
            {'task_id': task.task_id}
        ).fetchall()
        assistant_list = [a[1] for a in assistants_query]
        
        tasks_response.append({
            'task_id': task.task_id,
            'name': task.name,
            'assignee': assignee_name,
            'assistant': assistant_list,
            'start_date': task.start_date.isoformat() if task.start_date else None,
            'end_date': task.end_date.isoformat() if task.end_date else None,
            'completed': task.completed,
            'timeline_id': task.timeline_id,
            'remark': task.task_remark,
            'isWork': task.isWork
        })
    
    return jsonify(tasks_response), 200

@timelines_bp.route('/tasks/<int:task_id>/upload', methods=['POST'])
@jwt_required()
def upload_task_file(task_id):
    """上傳任務檔案"""
    user_id = int(get_jwt_identity())
    
    if 'file' not in request.files:
        return jsonify({'error': '沒有選擇檔案'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '檔案名稱為空'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '不支援的檔案格式'}), 400
    
    filename = secure_filename(file.filename)
    upload_folder = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'task_files')
    os.makedirs(upload_folder, exist_ok=True)
    
    import time
    unique_filename = f"{int(time.time())}_{filename}"
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    
    task_file = TaskFile(
        task_id=task_id,
        filename=unique_filename,
        original_filename=filename,
        file_path=file_path,
        file_size=os.path.getsize(file_path),
        uploaded_by=user_id
    )
    
    try:
        db.session.add(task_file)
        db.session.commit()
        return jsonify({
            'message': '檔案上傳成功',
            'filename': unique_filename,
            'original_filename': filename
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@timelines_bp.route('/tasks/<int:task_id>/files', methods=['GET'])
@jwt_required()
def get_task_files(task_id):
    """取得任務的所有檔案"""
    files = TaskFile.query.filter_by(task_id=task_id).all()
    
    return jsonify([{
        'id': f.id,
        'filename': f.filename,
        'original_filename': f.original_filename,
        'file_size': f.file_size,
        'uploaded_at': f.uploaded_at.isoformat() if f.uploaded_at else None
    } for f in files]), 200

@timelines_bp.route('/files/<filename>', methods=['GET'])
@jwt_required()
def download_file(filename):
    """下載檔案"""
    upload_folder = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'task_files')
    return send_from_directory(upload_folder, filename, as_attachment=True)

@timelines_bp.route('/tasks/<int:task_id>/comments', methods=['GET'])
@jwt_required()
def get_task_comments(task_id):
    """取得任務留言"""
    comments_query = db.session.execute(
        text("""
            SELECT c.id as comment_id, c.user_id, u.name as user_name, c.message as task_message
            FROM task_comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.task_id = :task_id
            ORDER BY c.created_at ASC
        """),
        {'task_id': task_id}
    ).fetchall()
    
    comments = [{
        'comment_id': c[0],
        'user_id': c[1],
        'user_name': c[2],
        'task_message': c[3]
    } for c in comments_query]
    
    return jsonify(comments), 200

@timelines_bp.route('/tasks/<int:task_id>/comments', methods=['POST'])
@jwt_required()
def add_task_comment(task_id):
    """新增任務留言"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    message = data.get('task_message')
    
    if not message or not isinstance(message, str):
        return jsonify({'error': '留言內容必須是字串'}), 400
    
    try:
        db.session.execute(
            text("""
                INSERT INTO task_comments (task_id, user_id, message, created_at)
                VALUES (:task_id, :user_id, :message, datetime('now'))
            """),
            {'task_id': task_id, 'user_id': user_id, 'message': message}
        )
        db.session.commit()
        return jsonify({'message': '留言新增成功'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@timelines_bp.route('/<int:timeline_id>/remark', methods=['PUT'])
@jwt_required()
def update_timeline_remark(timeline_id):
    """修改專案備註"""
    user_id = int(get_jwt_identity())
    timeline = Timeline.query.filter_by(id=timeline_id, user_id=user_id).first()
    
    if not timeline:
        return jsonify({'error': '找不到該專案'}), 404
    
    data = request.get_json()
    remark = data.get('remark', '')
    
    if not isinstance(remark, str):
        return jsonify({'error': '備註必須是字串'}), 400
    
    try:
        timeline.remark = remark
        db.session.commit()
        return jsonify({'message': '備註更新成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@timelines_bp.route('/search_user', methods=['POST'])
@jwt_required()
def search_user_by_email():
    """根據 Email 搜尋使用者"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': '請提供 Email'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'error': '找不到該使用者'}), 404
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email
    }), 200

@timelines_bp.route('/<int:timeline_id>/members', methods=['POST'])
@jwt_required()
def add_timeline_member(timeline_id):
    """邀請人員加入專案"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    invited_user_id = data.get('user_id')
    role = data.get('role', 1)  # 預設為成員
    
    if not invited_user_id:
        return jsonify({'error': '請提供使用者 ID'}), 400
    
    try:
        db.session.execute(
            text("""
                INSERT INTO timeline_users (timeline_id, user_id, role)
                VALUES (:timeline_id, :user_id, :role)
            """),
            {'timeline_id': timeline_id, 'user_id': invited_user_id, 'role': role}
        )
        db.session.commit()
        return jsonify({'message': '成員新增成功'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
