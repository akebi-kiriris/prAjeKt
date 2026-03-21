from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.task import Task
from models.task_user import TaskUser
from models.task_comment import TaskComment
from models.timeline_user import TimelineUser
from models.subtask import Subtask
from models.user import User
from datetime import datetime
import os
from services.task_service import (
    TASK_CREATE_ALLOWED_FIELDS,
    TASK_UPDATE_ALLOWED_FIELDS,
    TASK_STATUS_VALUES,
    build_task_member_list,
    can_manage_task_members,
    create_notification,
    find_unknown_fields,
    get_user_task_role,
    require_task_role,
    task_comment_to_dict,
    task_list_item_to_dict,
)

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('', methods=['GET'])
@jwt_required()
def get_tasks():
    """取得使用者的所有任務（包含被指派的）"""
    user_id = int(get_jwt_identity())
    
    # 取得自己建立的任務
    own_tasks = Task.query.filter_by(user_id=user_id).filter(Task.deleted_at.is_(None)).all()
    # 取得明確被指派的任務（在 task_users 表中）
    assigned_task_ids = [tu.task_id for tu in TaskUser.query.filter_by(user_id=user_id).all()]
    assigned_tasks = Task.query.filter(Task.task_id.in_(assigned_task_ids), Task.deleted_at.is_(None)).all() if assigned_task_ids else []

    # 合併並去重
    all_tasks = {t.task_id: t for t in own_tasks + assigned_tasks}
    tasks = sorted(all_tasks.values(), key=lambda t: (t.completed, t.end_date or datetime.max))
    
    result = []
    for t in tasks:
        member_list, current_user_role = build_task_member_list(t.task_id, viewer_user_id=user_id)

        # 若在 task_users 找不到，試從 timeline_users 取得角色
        if current_user_role is None and t.timeline_id:
            tl_member = TimelineUser.query.filter_by(timeline_id=t.timeline_id, user_id=user_id).first()
            if tl_member:
                current_user_role = tl_member.role

        # is_owner： task_users 或 timeline_users 中 role=0，或者是任務的建立者
        is_owner = (current_user_role == 0) or (t.user_id == user_id)
        
        # 取得子任務
        subtasks = Subtask.query.filter_by(task_id=t.task_id).order_by(Subtask.sort_order).all()
        subtask_list = [s.to_dict() for s in subtasks]

        result.append(task_list_item_to_dict(t, member_list, subtask_list, is_owner))
    
    return jsonify(result), 200

@tasks_bp.route('', methods=['POST'])
@jwt_required()
def create_task():
    """新增任務"""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    if not isinstance(data, dict):
        return jsonify({'error': '請提供正確的 JSON 物件'}), 400

    unknown_fields = find_unknown_fields(data, TASK_CREATE_ALLOWED_FIELDS)
    if unknown_fields:
        return jsonify({'error': f'不允許的欄位: {", ".join(unknown_fields)}'}), 400
    
    if not data.get('name') or not data.get('end_date'):
        return jsonify({'error': '請提供標題和截止日期'}), 400

    status = data.get('status', 'pending')
    if status not in TASK_STATUS_VALUES:
        return jsonify({'error': 'status 欄位值不合法'}), 400

    try:
        priority = int(data.get('priority', 2))
    except (TypeError, ValueError):
        return jsonify({'error': 'priority 必須是數字'}), 400

    if priority < 1 or priority > 3:
        return jsonify({'error': 'priority 必須介於 1 到 3'}), 400

    try:
        start_date = datetime.fromisoformat(data['start_date']) if data.get('start_date') else None
    except ValueError:
        return jsonify({'error': 'start_date 格式錯誤'}), 400

    try:
        end_date = datetime.fromisoformat(data['end_date'])
    except (TypeError, ValueError):
        return jsonify({'error': 'end_date 格式錯誤'}), 400

    new_task = Task(
        user_id=user_id,
        name=data['name'],
        timeline_id=data.get('timeline_id'),
        priority=priority,
        status=status,
        tags=data.get('tags'),
        estimated_hours=data.get('estimated_hours'),
        start_date=start_date,
        end_date=end_date,
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
        
        db.session.commit()
        return jsonify({'message': '任務新增成功', 'task_id': new_task.task_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
@require_task_role('member')
def update_task(task_id):
    """更新任務"""
    task = Task.query.filter_by(task_id=task_id).filter(Task.deleted_at.is_(None)).first()
    
    if not task:
        return jsonify({'error': '找不到該任務'}), 404
    
    data = request.get_json() or {}

    if not isinstance(data, dict):
        return jsonify({'error': '請提供正確的 JSON 物件'}), 400

    unknown_fields = find_unknown_fields(data, TASK_UPDATE_ALLOWED_FIELDS)
    if unknown_fields:
        return jsonify({'error': f'不允許的欄位: {", ".join(unknown_fields)}'}), 400

    if 'status' in data and data['status'] not in TASK_STATUS_VALUES:
        return jsonify({'error': 'status 欄位值不合法'}), 400

    if 'priority' in data:
        try:
            priority = int(data['priority'])
        except (TypeError, ValueError):
            return jsonify({'error': 'priority 必須是數字'}), 400
        if priority < 1 or priority > 3:
            return jsonify({'error': 'priority 必須介於 1 到 3'}), 400
        task.priority = priority
    
    if 'name' in data:
        if not data['name'] or not str(data['name']).strip():
            return jsonify({'error': 'name 不可為空'}), 400
        task.name = str(data['name']).strip()

    if 'timeline_id' in data:
        task.timeline_id = data['timeline_id']

    if 'status' in data:
        task.status = data['status']

    if 'tags' in data:
        task.tags = data['tags']

    if 'estimated_hours' in data:
        task.estimated_hours = data['estimated_hours']

    if 'actual_hours' in data:
        task.actual_hours = data['actual_hours']

    if 'task_remark' in data:
        task.task_remark = data['task_remark']

    if 'isWork' in data:
        task.isWork = data['isWork']
    
    if 'start_date' in data:
        if data['start_date']:
            try:
                task.start_date = datetime.fromisoformat(data['start_date'])
            except ValueError:
                return jsonify({'error': 'start_date 格式錯誤'}), 400
        else:
            task.start_date = None

    if 'end_date' in data:
        if data['end_date']:
            try:
                task.end_date = datetime.fromisoformat(data['end_date'])
            except ValueError:
                return jsonify({'error': 'end_date 格式錯誤'}), 400
        else:
            task.end_date = None
    
    try:
        db.session.commit()
        return jsonify({'message': '任務更新成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
@require_task_role('owner')
def delete_task(task_id):
    """刪除任務（軟刪除）"""
    task = Task.query.filter_by(task_id=task_id).filter(Task.deleted_at.is_(None)).first()
    
    if not task:
        return jsonify({'error': '找不到該任務'}), 404
    
    try:
        task.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': '任務刪除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>/toggle', methods=['PATCH'])
@jwt_required()
@require_task_role('member')
def toggle_task(task_id):
    """切換任務完成狀態"""
    task = Task.query.filter_by(task_id=task_id).filter(Task.deleted_at.is_(None)).first()
    
    if not task:
        return jsonify({'error': '找不到該任務'}), 404
    
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
@require_task_role('member')
def get_task_members(task_id):
    """取得任務成員列表"""
    result, _ = build_task_member_list(task_id, include_contact=True)
    return jsonify(result), 200

@tasks_bp.route('/<int:task_id>/members', methods=['POST'])
@jwt_required()
def add_task_member(task_id):
    """新增任務成員（任務負責人 或 所屬 timeline 的負責人 可操作）"""
    user_id = int(get_jwt_identity())
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': '找不到該任務'}), 404

    if not can_manage_task_members(user_id, task):
        return jsonify({'error': '只有負責人可新增成員'}), 403

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
        # 通知被指派的成員
        task = Task.query.get(task_id)
        actor = User.query.get(int(get_jwt_identity()))
        actor_name = actor.name if actor else '某人'
        task_name = task.name if task else '任務'
        create_notification(
            user_id=new_user_id,
            ntype='task_assigned',
            title=f'你被指派到任務「{task_name}」',
            content=f'{actor_name} 將你加入任務「{task_name}」',
            link=f'/tasks'
        )
        db.session.commit()
        return jsonify({'message': '成員新增成功'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>/members/<int:member_id>', methods=['DELETE'])
@jwt_required()
@require_task_role('owner')
def remove_task_member(task_id, member_id):
    """移除任務成員"""
    target = TaskUser.query.filter_by(task_id=task_id, user_id=member_id).first()
    if target and target.role == 0:
        return jsonify({'error': '無法移除負責人'}), 400
    
    try:
        TaskUser.query.filter_by(task_id=task_id, user_id=member_id).delete()
        db.session.commit()
        return jsonify({'message': '成員移除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@tasks_bp.route('/<int:task_id>/members/<int:member_id>', methods=['PATCH'])
@jwt_required()
def update_task_member_role(task_id, member_id):
    """更新任務成員角色。
    當 role=0 時，會把該任務其餘成員降為協作者，形成單一主責人。"""
    payload = request.get_json() or {}
    if not isinstance(payload, dict):
        return jsonify({'error': '請提供正確的 JSON 物件'}), 400

    if 'role' not in payload:
        return jsonify({'error': '請提供 role 欄位'}), 400

    try:
        new_role = int(payload.get('role'))
    except (TypeError, ValueError):
        return jsonify({'error': 'role 必須是數字'}), 400

    if new_role not in (0, 1):
        return jsonify({'error': 'role 只允許 0(負責人) 或 1(協作者)'}), 400

    task = Task.query.filter_by(task_id=task_id).first()
    if not task:
        return jsonify({'error': '找不到該任務'}), 404

    current_user_id = int(get_jwt_identity())
    if not can_manage_task_members(current_user_id, task):
        return jsonify({'error': '只有任務負責人、任務建立者或專案負責人可執行此操作'}), 403

    target = TaskUser.query.filter_by(task_id=task_id, user_id=member_id).first()
    if not target:
        # 允許專案成員直接被提升為任務主責人（會自動補 task_user）。
        if task.timeline_id:
            timeline_member = TimelineUser.query.filter_by(
                timeline_id=task.timeline_id,
                user_id=member_id
            ).first()
            if timeline_member is None:
                return jsonify({'error': '該使用者不是此專案成員，無法設為主責人'}), 400
        else:
            return jsonify({'error': '該使用者尚未加入任務，請先指派為成員'}), 400

        target = TaskUser(task_id=task_id, user_id=member_id, role=1)
        db.session.add(target)

    # 避免任務沒有主責人。
    if target.role == 0 and new_role == 1:
        return jsonify({'error': '無法直接降級現任負責人，請先指定新負責人'}), 400

    try:
        if new_role == 0:
            TaskUser.query.filter_by(task_id=task_id).update({'role': 1})
            target.role = 0

        db.session.commit()
        return jsonify({'message': '成員角色更新成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===== 任務留言 API =====

@tasks_bp.route('/<int:task_id>/comments', methods=['GET'])
@jwt_required()
@require_task_role('member')
def get_task_comments(task_id):
    """取得任務留言"""
    comments = TaskComment.query.filter_by(task_id=task_id).filter(TaskComment.deleted_at.is_(None)).order_by(TaskComment.created_at.desc()).all()
    result = []
    for c in comments:
        user = User.query.get(c.user_id)
        result.append(task_comment_to_dict(c, user))
    return jsonify(result), 200

@tasks_bp.route('/<int:task_id>/comments', methods=['POST'])
@jwt_required()
@require_task_role('member')
def add_task_comment(task_id):
    """新增任務留言"""
    user_id = int(get_jwt_identity())
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
        # 通知任務所有其他成員有新留言
        actor = User.query.get(user_id)
        task = Task.query.get(task_id)
        actor_name = actor.name if actor else '某人'
        task_name = task.name if task else '任務'
        members = TaskUser.query.filter_by(task_id=task_id).all()
        notified_ids = {m.user_id for m in members} - {user_id}
        # 若無明確成員，嘗試從 timeline 成員通知
        if not notified_ids and task and task.timeline_id:
            tl_members = TimelineUser.query.filter_by(timeline_id=task.timeline_id).all()
            notified_ids = {m.user_id for m in tl_members} - {user_id}
        for uid in notified_ids:
            create_notification(
                user_id=uid,
                ntype='comment',
                title=f'「{task_name}」有新留言',
                content=f'{actor_name}：{message[:50]}',
                link=f'/tasks'
            )
        db.session.commit()
        user = User.query.get(user_id)
        return jsonify({
            'comment_id': comment.comment_id,
            'user_id': user_id,
            'user_name': user.name if user else '未知',
            'task_message': message,
            'created_at': comment.created_at.isoformat() + 'Z' if comment.created_at else None,
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_task_comment(task_id, comment_id):
    """刪除任務留言（軟刪除）"""
    user_id = int(get_jwt_identity())
    comment = TaskComment.query.filter_by(comment_id=comment_id, task_id=task_id).filter(TaskComment.deleted_at.is_(None)).first()
    
    if not comment:
        return jsonify({'error': '找不到該留言'}), 404
    
    if comment.user_id != user_id:
        return jsonify({'error': '只能刪除自己的留言'}), 403
    
    try:
        comment.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': '留言刪除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ===== 任務檔案 API =====

ALLOWED_FILE_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'webp',
    'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'zip', 'csv', 'mp4', 'mov'
}

def allowed_task_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_FILE_EXTENSIONS

@tasks_bp.route('/<int:task_id>/files', methods=['GET'])
@jwt_required()
@require_task_role('member')
def get_task_files(task_id):
    """取得任務所有附件"""
    from models.timeline import TaskFile
    files = TaskFile.query.filter_by(task_id=task_id).order_by(TaskFile.uploaded_at.desc()).all()
    result = []
    for f in files:
        uploader = User.query.get(f.uploaded_by)
        result.append({
            'id': f.id,
            'filename': f.filename,
            'original_filename': f.original_filename,
            'file_size': f.file_size,
            'uploaded_at': f.uploaded_at.isoformat() + 'Z' if f.uploaded_at else None,
            'uploaded_by_name': uploader.name if uploader else '未知',
        })
    return jsonify(result), 200

@tasks_bp.route('/<int:task_id>/upload', methods=['POST'])
@jwt_required()
@require_task_role('member')
def upload_task_file(task_id):
    """上傳任務附件"""
    import time
    from models.timeline import TaskFile
    from werkzeug.utils import secure_filename

    user_id = int(get_jwt_identity())

    if 'file' not in request.files:
        return jsonify({'error': '沒有選擇檔案'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '檔案名稱為空'}), 400
    if not allowed_task_file(file.filename):
        return jsonify({'error': '不支援的檔案格式'}), 400

    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    if file_size > 10 * 1024 * 1024:
        return jsonify({'error': '檔案大小不可超過 10MB'}), 400

    original_filename = file.filename  # 保留原始檔名（含中文）用於顯示
    filename = secure_filename(file.filename)  # 安全檔名用於存磁碟
    if not filename or filename.startswith('.'):
        # secure_filename 把中文全濾掉時，用時間戳加副檔名當備援
        ext = original_filename.rsplit('.', 1)[-1] if '.' in original_filename else 'bin'
        filename = f"file.{ext}"
    upload_folder = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'task_files')
    os.makedirs(upload_folder, exist_ok=True)
    unique_filename = f"{int(time.time())}_{filename}"
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)

    task_file = TaskFile(
        task_id=task_id,
        filename=unique_filename,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        uploaded_by=user_id
    )
    try:
        db.session.add(task_file)
        db.session.commit()
        return jsonify({
            'id': task_file.id,
            'message': '檔案上傳成功',
            'filename': unique_filename,
            'original_filename': filename,
            'file_size': file_size,
            'uploaded_at': task_file.uploaded_at.isoformat() + 'Z' if task_file.uploaded_at else None,
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>/files/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_task_file(task_id, file_id):
    """刪除任務附件（上傳者或負責人可刪除）"""
    from models.timeline import TaskFile
    user_id = int(get_jwt_identity())
    role = get_user_task_role(user_id, task_id)
    if role is None:
        return jsonify({'error': '你沒有權限存取此任務'}), 403

    task_file = TaskFile.query.filter_by(id=file_id, task_id=task_id).first()
    if not task_file:
        return jsonify({'error': '找不到該檔案'}), 404
    if task_file.uploaded_by != user_id and role != 0:
        return jsonify({'error': '只有上傳者或負責人可刪除檔案'}), 403

    try:
        if task_file.file_path and os.path.exists(task_file.file_path):
            os.remove(task_file.file_path)
        db.session.delete(task_file)
        db.session.commit()
        return jsonify({'message': '檔案刪除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/files/<filename>', methods=['GET'])
def download_task_file(filename):
    """下載/預覽任務附件（以原始檔名呈現）"""
    from models.timeline import TaskFile
    upload_folder = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'task_files')
    task_file = TaskFile.query.filter_by(filename=filename).first()
    original_name = task_file.original_filename if task_file else filename
    return send_from_directory(upload_folder, filename, as_attachment=False, download_name=original_name)

@tasks_bp.route('/<int:task_id>/subtasks', methods=['GET'])
@jwt_required()
@require_task_role('member')
def get_subtasks(task_id):
    """取得任務的所有子任務"""
    subtasks = Subtask.query.filter_by(task_id=task_id).order_by(Subtask.sort_order).all()
    return jsonify([s.to_dict() for s in subtasks]), 200

@tasks_bp.route('/<int:task_id>/subtasks', methods=['POST'])
@jwt_required()
@require_task_role('member')
def create_subtask(task_id):
    """新增子任務"""
    data = request.get_json()
    name = data.get('name')
    
    if not name:
        return jsonify({'error': '請提供子任務名稱'}), 400
    
    # 取得最大排序順序
    max_order = db.session.query(db.func.max(Subtask.sort_order)).filter_by(task_id=task_id).scalar() or 0
    
    try:
        subtask = Subtask(
            task_id=task_id,
            name=name.strip(),
            sort_order=max_order + 1
        )
        db.session.add(subtask)
        db.session.commit()
        return jsonify({'message': '子任務新增成功', 'subtask': subtask.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>/subtasks/<int:subtask_id>', methods=['PUT'])
@jwt_required()
@require_task_role('member')
def update_subtask(task_id, subtask_id):
    """更新子任務"""
    subtask = Subtask.query.filter_by(id=subtask_id, task_id=task_id).first()
    
    if not subtask:
        return jsonify({'error': '找不到該子任務'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        subtask.name = data['name']
    if 'completed' in data:
        subtask.completed = data['completed']
    if 'sort_order' in data:
        subtask.sort_order = data['sort_order']
    
    try:
        db.session.commit()
        return jsonify({'message': '子任務更新成功', 'subtask': subtask.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>/subtasks/<int:subtask_id>', methods=['DELETE'])
@jwt_required()
@require_task_role('member')
def delete_subtask(task_id, subtask_id):
    """刪除子任務"""
    subtask = Subtask.query.filter_by(id=subtask_id, task_id=task_id).first()
    
    if not subtask:
        return jsonify({'error': '找不到該子任務'}), 404
    
    try:
        db.session.delete(subtask)
        db.session.commit()
        return jsonify({'message': '子任務刪除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>/subtasks/<int:subtask_id>/toggle', methods=['PATCH'])
@jwt_required()
@require_task_role('member')
def toggle_subtask(task_id, subtask_id):
    """切換子任務完成狀態"""
    subtask = Subtask.query.filter_by(id=subtask_id, task_id=task_id).first()
    
    if not subtask:
        return jsonify({'error': '找不到該子任務'}), 404
    
    subtask.completed = not subtask.completed
    
    try:
        db.session.commit()
        return jsonify({'message': '狀態更新成功', 'subtask': subtask.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ===== 任務狀態更新 API (看板用) =====

@tasks_bp.route('/<int:task_id>/status', methods=['PATCH'])
@jwt_required()
@require_task_role('member')
def update_task_status(task_id):
    """更新任務狀態（看板拖曳用）"""
    task = Task.query.filter_by(task_id=task_id).filter(Task.deleted_at.is_(None)).first()
    
    if not task:
        return jsonify({'error': '找不到該任務'}), 404
    
    data = request.get_json()
    new_status = data.get('status')
    
    valid_statuses = ['pending', 'in_progress', 'completed']
    if new_status not in valid_statuses:
        return jsonify({'error': f'無效的狀態，有效值為: {valid_statuses}'}), 400
    
    task.status = new_status
    task.completed = (new_status == 'completed')
    
    try:
        db.session.commit()
        return jsonify({'message': '狀態更新成功', 'status': task.status, 'completed': task.completed}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@tasks_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_tasks():
    """取得即將到期（3天內）或時間進度超過80%的任務"""
    from datetime import timedelta
    from sqlalchemy import or_
    user_id = int(get_jwt_identity())
    today = datetime.utcnow().date()
    threshold = today + timedelta(days=3)

    user_timeline_ids = [tu.timeline_id for tu in TimelineUser.query.filter_by(user_id=user_id).all()]
    assigned_task_ids = [tu.task_id for tu in TaskUser.query.filter_by(user_id=user_id).all()]

    conditions = [Task.user_id == user_id]
    if assigned_task_ids:
        conditions.append(Task.task_id.in_(assigned_task_ids))
    if user_timeline_ids:
        conditions.append(Task.timeline_id.in_(user_timeline_ids))

    tasks = Task.query.filter(
        Task.deleted_at.is_(None),
        Task.completed == False,
        Task.end_date.isnot(None),
        or_(*conditions)
    ).all()

    result = []
    for t in tasks:
        end = t.end_date.date() if hasattr(t.end_date, 'date') else t.end_date

        upcoming = end <= threshold
        if not upcoming and t.start_date:
            start = t.start_date.date() if hasattr(t.start_date, 'date') else t.start_date
            total = (end - start).days
            if total > 0 and (today - start).days / total >= 0.8:
                upcoming = True

        if upcoming:
            result.append({
                'task_id': t.task_id,
                'name': t.name,
                'end_date': end.isoformat(),
                'priority': t.priority,
                'timeline_id': t.timeline_id,
                'is_overdue': end < today,
                'type': 'task',
            })

    return jsonify(result), 200
