from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.timeline import Timeline
from models.timeline_user import TimelineUser
from models.task import Task
from models.task_user import TaskUser
from models.user import User
from models.notification import Notification
from datetime import datetime
import os
import json
import google.generativeai as genai
from services.timeline_service import (
    TIMELINE_UPDATE_ALLOWED_FIELDS,
    find_unknown_fields,
    get_task_access,
    get_user_timeline_role,
    require_timeline_role,
    timeline_list_item_to_dict,
    timeline_member_item_to_dict,
    timeline_task_item_to_dict,
)

timelines_bp = Blueprint('timelines', __name__)

@timelines_bp.route('', methods=['GET'])
@jwt_required()
def get_timelines():
    """取得使用者的所有專案時程（包含被邀請的）"""
    user_id = int(get_jwt_identity())

    # 查詢使用者參與的所有專案（自己建立的 + 被邀請的）
    memberships = db.session.query(Timeline, TimelineUser.role)\
        .join(TimelineUser, Timeline.id == TimelineUser.timeline_id)\
        .filter(TimelineUser.user_id == user_id, Timeline.deleted_at.is_(None))\
        .order_by(Timeline.id.desc())\
        .all()

    if not memberships:
        return jsonify([]), 200

    timeline_ids = [timeline.id for timeline, _ in memberships]

    # 單一批次查詢：取得每個 timeline 的總任務數與已完成任務數
    task_counts = db.session.query(
        Task.timeline_id,
        db.func.count(Task.task_id).label('total'),
        db.func.sum(db.cast(Task.completed, db.Integer)).label('completed')
    ).filter(
        Task.timeline_id.in_(timeline_ids),
        Task.deleted_at.is_(None)
    ).group_by(Task.timeline_id).all()

    counts_map = {row.timeline_id: (row.total, row.completed or 0) for row in task_counts}

    result = []
    for timeline, role in memberships:
        total_tasks, completed_tasks = counts_map.get(timeline.id, (0, 0))
        result.append(timeline_list_item_to_dict(timeline, role, total_tasks, completed_tasks))

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
        db.session.flush()  # 先取得 new_timeline.id，尚未 commit
        # 建立者自動成為負責人（role=0）
        db.session.add(TimelineUser(timeline_id=new_timeline.id, user_id=user_id, role=0))
        db.session.commit()
        return jsonify({'message': '專案新增成功', 'id': new_timeline.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@timelines_bp.route('/<int:timeline_id>', methods=['PUT'])
@jwt_required()
@require_timeline_role('member')
def update_timeline(timeline_id):
    """更新專案時程（負責人或協作者均可）"""
    timeline = Timeline.query.filter_by(id=timeline_id).filter(Timeline.deleted_at.is_(None)).first()

    if not timeline:
        return jsonify({'error': '找不到該專案'}), 404
    
    data = request.get_json() or {}

    if not isinstance(data, dict):
        return jsonify({'error': '請提供正確的 JSON 物件'}), 400

    unknown_fields = find_unknown_fields(data, TIMELINE_UPDATE_ALLOWED_FIELDS)
    if unknown_fields:
        return jsonify({'error': f'不允許的欄位: {", ".join(unknown_fields)}'}), 400
    
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
@require_timeline_role('owner')
def delete_timeline(timeline_id):
    """刪除專案時程（軟刪除，僅負責人可操作）"""
    timeline = Timeline.query.filter_by(id=timeline_id).filter(Timeline.deleted_at.is_(None)).first()

    if not timeline:
        return jsonify({'error': '找不到該專案'}), 404

    try:
        # 軟刪除專案
        timeline.deleted_at = datetime.utcnow()

        # 連帶軟刪除該專案下的所有任務
        Task.query.filter_by(timeline_id=timeline_id).update({'deleted_at': datetime.utcnow()})
        
        db.session.commit()
        return jsonify({'message': '專案刪除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@timelines_bp.route('/<int:timeline_id>/tasks', methods=['GET'])
@jwt_required()
@require_timeline_role('member')
def get_timeline_tasks(timeline_id):
    """取得專案的所有任務（含負責人、助理資訊）"""
    tasks = Task.query.filter_by(timeline_id=timeline_id).filter(Task.deleted_at.is_(None)).order_by(Task.end_date).all()

    if not tasks:
        return jsonify([]), 200

    task_ids = [t.task_id for t in tasks]

    # 批次查詢所有相關的 TaskUser 與 User，避免 N+1
    task_users = db.session.query(TaskUser, User)\
        .join(User, TaskUser.user_id == User.id)\
        .filter(TaskUser.task_id.in_(task_ids))\
        .all()

    # 建立 task_id -> assignee_name 與 task_id -> assistant_names 的映射
    assignee_map = {}   # task_id -> str
    assistant_map = {}  # task_id -> list[str]
    for tu, user in task_users:
        if tu.role == 0:
            assignee_map[tu.task_id] = user.name
        elif tu.role == 1:
            assistant_map.setdefault(tu.task_id, []).append(user.name)

    tasks_response = []
    for task in tasks:
        assignee_name = assignee_map.get(task.task_id)
        assistant_list = assistant_map.get(task.task_id, [])
        tasks_response.append(timeline_task_item_to_dict(task, assignee_name, assistant_list))

    return jsonify(tasks_response), 200

@timelines_bp.route('/<int:timeline_id>/remark', methods=['PUT'])
@jwt_required()
@require_timeline_role('member')
def update_timeline_remark(timeline_id):
    """修改專案備註（負責人或協作者均可）"""
    timeline = Timeline.query.filter_by(id=timeline_id).filter(Timeline.deleted_at.is_(None)).first()

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

@timelines_bp.route('/<int:timeline_id>/members', methods=['GET'])
@jwt_required()
@require_timeline_role('member')
def get_timeline_members(timeline_id):
    """取得專案成員列表（成員皆可查）"""
    members = TimelineUser.query.filter_by(timeline_id=timeline_id).all()
    if not members:
        return jsonify([]), 200

    # 批次查詢所有成員的 User 資料，避免 N+1
    member_ids = [m.user_id for m in members]
    users_map = {u.id: u for u in User.query.filter(User.id.in_(member_ids)).all()}

    result = []
    for m in members:
        user = users_map.get(m.user_id)
        if user:
            result.append(timeline_member_item_to_dict(m, user))
    return jsonify(result), 200


@timelines_bp.route('/<int:timeline_id>/members', methods=['POST'])
@jwt_required()
@require_timeline_role('owner')
def add_timeline_member(timeline_id):
    """邀請人員加入專案（僅負責人可操作）"""
    data = request.get_json()
    invited_user_id = data.get('user_id')
    role = data.get('role', 1)  # 預設為成員
    
    if not invited_user_id:
        return jsonify({'error': '請提供使用者 ID'}), 400
    
    try:
        member = TimelineUser(timeline_id=timeline_id, user_id=invited_user_id, role=role)
        db.session.add(member)
        # 通知被邀請的成員
        actor = User.query.get(int(get_jwt_identity()))
        timeline = Timeline.query.get(timeline_id)
        actor_name = actor.name if actor else '某人'
        timeline_name = timeline.name if timeline else '專案'
        notif = Notification(
            user_id=invited_user_id,
            type='timeline_invited',
            title=f'你被邀請加入專案「{timeline_name}」',
            content=f'{actor_name} 邀請你加入「{timeline_name}」',
            link='/timelines'
        )
        db.session.add(notif)
        db.session.commit()
        return jsonify({'message': '成員新增成功'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@timelines_bp.route('/<int:timeline_id>/members/<int:member_user_id>', methods=['DELETE'])
@jwt_required()
@require_timeline_role('owner')
def remove_timeline_member(timeline_id, member_user_id):
    """將成員移出專案（僅負責人可操作，且不能移除自己）"""
    user_id = int(get_jwt_identity())

    if member_user_id == user_id:
        return jsonify({'error': '不能將自己移出專案'}), 400

    try:
        member = TimelineUser.query.filter_by(timeline_id=timeline_id, user_id=member_user_id).first()
        if not member or member.role == 0:
            return jsonify({'error': '找不到該成員，或無法移除負責人'}), 404
        db.session.delete(member)
        db.session.commit()
        return jsonify({'message': '成員已移除'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ===== AI 任務生成 API =====

@timelines_bp.route('/<int:timeline_id>/generate-tasks', methods=['POST'])
@jwt_required()
@require_timeline_role('member')
def generate_tasks_with_ai(timeline_id):
    """使用 AI 自動生成任務清單（負責人或協作者均可）"""
    timeline = Timeline.query.filter_by(id=timeline_id).filter(Timeline.deleted_at.is_(None)).first()
    if not timeline:
        return jsonify({'error': '找不到該專案'}), 404
    
    data = request.get_json() or {}
    project_name = data.get('name', timeline.name)
    description = data.get('description', timeline.remark or '')
    
    if not project_name.strip():
        return jsonify({'error': '請提供專案名稱'}), 400
    
    # 查詢現有任務
    existing_tasks = Task.query.filter_by(timeline_id=timeline_id).filter(Task.deleted_at.is_(None)).all()
    existing_tasks_info = []
    for task in existing_tasks:
        existing_tasks_info.append({
            'task_id': task.task_id,
            'name': task.name,
            'priority': task.priority,
            'estimated_days': (task.end_date - task.start_date).days if task.start_date and task.end_date else 3,
            'task_remark': task.task_remark or '',
            'isExisting': True
        })
    
    try:
        # 初始化 Gemini AI
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return jsonify({'error': 'Google API Key 未配置，請在 .env 中設定 GOOGLE_API_KEY'}), 500
        
        genai.configure(api_key=api_key)
        
        # 定義 JSON Schema 來限定輸出格式
        task_schema = {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "任務名稱（10-30字，繁體中文）"},
                        "priority": {"type": "integer", "description": "優先級（1=高,2=中,3=低）", "enum": [1,2,3]},
                        "estimated_days": {"type": "integer", "description": "預估完成天數"},
                        "task_remark": {"type": "string", "description": "任務備註（20-50字，繁體中文）"}
                    },
                    "required": ["name", "priority", "estimated_days", "task_remark"]
                }
        }
        
        # 建構 Prompt（包含現有任務資訊）
        existing_tasks_text = ""
        if existing_tasks_info:
            existing_tasks_text = "\n\n現有任務：\n"
            for idx, task in enumerate(existing_tasks_info, 1):
                existing_tasks_text += f"{idx}. {task['name']} (優先級:{task['priority']}, 預估:{task['estimated_days']}天)\n"
        
        prompt = f"""你是一個專業的專案管理助手。請根據以下專案資訊，為使用者生成合理的任務清單。

                專案名稱: {project_name}
                專案描述: {description if description.strip() else '無'}{existing_tasks_text}

                要求：
                1. 如果有現有任務，請參考它們來生成互補的任務（避免重複，找出缺失環節）
                2. 如果沒有現有任務，請生成數個完整的任務
                3. 生成的任務要考慮現有任務的優先級和邏輯順序

                請務必回傳一個 JSON 陣列，每個任務物件必須包含以下欄位：
                1. name（string）：任務名稱，10-30字，繁體中文
                2. priority（integer）：優先級，1=高，2=中，3=低
                3. estimated_days（integer）：預估完成天數，根據任務複雜度合理估計
                4. task_remark（string）：任務備註，20-50字，繁體中文

                不要使用 task_name、priority: "高" 這種格式，請嚴格依照上方欄位與型別。
                按照邏輯順序排列（從準備、進行、到完成）
                """
        
        # 呼叫 AI，使用 response_mime_type 限定 JSON 輸出
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.7
            }
        )
        
        # 直接解析 JSON（不需要手動處理 markdown 符號）
        ai_generated_tasks = json.loads(response.text)
        
        # 驗證回傳格式
        if not isinstance(ai_generated_tasks, list):
            return jsonify({'error': 'AI 回傳格式錯誤'}), 500
        
        # 補充預設值並標記為 AI 生成
        for task in ai_generated_tasks:
            task['timeline_id'] = timeline_id
            task['status'] = 'pending'
            task['completed'] = False
            task['isExisting'] = False  # 標記為 AI 生成的新任務
            task.setdefault('priority', 2)
            task.setdefault('estimated_days', 3)
            task.setdefault('task_remark', '')
        
        # 合併現有任務和 AI 生成任務
        all_tasks = existing_tasks_info + ai_generated_tasks
        
        return jsonify({
            'message': f'現有 {len(existing_tasks_info)} 個任務，AI 生成 {len(ai_generated_tasks)} 個新任務',
            'tasks': all_tasks,
            'existingCount': len(existing_tasks_info),
            'generatedCount': len(ai_generated_tasks)
        }), 200

    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'AI 回應解析失敗',
            'detail': str(e)
        }), 500
    except Exception as e:
        return jsonify({'error': f'AI 生成失敗: {str(e)}'}), 500


@timelines_bp.route('/<int:timeline_id>/batch-create-tasks', methods=['POST'])
@jwt_required()
@require_timeline_role('member')
def batch_create_tasks(timeline_id):
    """批量創建任務（用於 AI 生成後確認）"""
    user_id = int(get_jwt_identity())

    timeline = Timeline.query.filter_by(id=timeline_id).filter(Timeline.deleted_at.is_(None)).first()
    if not timeline:
        return jsonify({'error': '找不到該專案'}), 404
    
    data = request.get_json()
    tasks = data.get('tasks', [])
    
    if not isinstance(tasks, list) or len(tasks) == 0:
        return jsonify({'error': '請提供至少一個任務'}), 400
    
    try:
        from datetime import timedelta
        
        # 收集所有現有任務 ID 和使用者選中的現有任務 ID
        all_existing_task_ids = [t.task_id for t in Task.query.filter_by(timeline_id=timeline_id).filter(Task.deleted_at.is_(None)).all()]
        selected_existing_task_ids = [task['task_id'] for task in tasks if task.get('isExisting') and task.get('task_id')]
        
        # 軟刪除未被選中的舊任務
        tasks_to_delete = set(all_existing_task_ids) - set(selected_existing_task_ids)
        if tasks_to_delete:
            Task.query.filter(Task.task_id.in_(tasks_to_delete)).update({'deleted_at': datetime.utcnow()}, synchronize_session=False)
        
        # 新增 AI 生成的任務（isExisting=False）
        created_tasks = []
        start_date = timeline.start_date or datetime.now()
        current_date = start_date
        
        for task_data in tasks:
            # 跳過現有任務（已經存在於資料庫，不需要重複新增）
            if task_data.get('isExisting'):
                continue
            
            # 計算任務時間
            estimated_days = task_data.get('estimated_days', 3)
            end_date = current_date + timedelta(days=estimated_days)
            
            new_task = Task(
                user_id=user_id,
                timeline_id=timeline_id,
                name=task_data.get('name', '未命名任務'),
                priority=task_data.get('priority', 2),
                status=task_data.get('status', 'pending'),
                task_remark=task_data.get('task_remark', ''),
                start_date=current_date,
                end_date=end_date,
                completed=False,
                isWork=1
            )
            
            db.session.add(new_task)
            created_tasks.append(new_task.name)
            current_date = end_date
        
        db.session.commit()
        
        return jsonify({
            'message': f'保留 {len(selected_existing_task_ids)} 個舊任務，刪除 {len(tasks_to_delete)} 個舊任務，新增 {len(created_tasks)} 個任務',
            'kept': len(selected_existing_task_ids),
            'deleted': len(tasks_to_delete),
            'created': len(created_tasks)
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@timelines_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_timelines():
    """取得即將到期（3天內）或時間進度超過80%的專案"""
    from datetime import timedelta
    user_id = int(get_jwt_identity())
    today = datetime.utcnow().date()
    threshold = today + timedelta(days=3)

    memberships = db.session.query(Timeline, TimelineUser.role)\
        .join(TimelineUser, Timeline.id == TimelineUser.timeline_id)\
        .filter(TimelineUser.user_id == user_id, Timeline.deleted_at.is_(None))\
        .all()

    result = []
    for timeline, role in memberships:
        if not timeline.end_date:
            continue
        end = timeline.end_date.date() if hasattr(timeline.end_date, 'date') else timeline.end_date

        upcoming = end <= threshold
        if not upcoming and timeline.start_date:
            start = timeline.start_date.date() if hasattr(timeline.start_date, 'date') else timeline.start_date
            total = (end - start).days
            if total > 0 and (today - start).days / total >= 0.8:
                upcoming = True

        if upcoming:
            result.append({
                'id': timeline.id,
                'name': timeline.name,
                'end_date': end.isoformat(),
                'role': role,
                'is_overdue': end < today,
                'type': 'timeline',
            })

    return jsonify(result), 200


@timelines_bp.route('/<int:timeline_id>/member-stats', methods=['GET'])
@jwt_required()
@require_timeline_role('owner')
def get_member_stats(timeline_id):
    """取得專案成員任務統計（負責人限定）"""
    members = TimelineUser.query.filter_by(timeline_id=timeline_id).all()
    member_ids = [m.user_id for m in members]
    users_map = {u.id: u.name for u in User.query.filter(User.id.in_(member_ids)).all()}

    tasks = Task.query.filter(
        Task.timeline_id == timeline_id,
        Task.deleted_at.is_(None)
    ).all()
    task_ids = [t.task_id for t in tasks]

    # 各任務的被指派成員（task_users）
    task_user_map = {}  # task_id -> set of user_ids
    if task_ids:
        for tu in TaskUser.query.filter(TaskUser.task_id.in_(task_ids)).all():
            task_user_map.setdefault(tu.task_id, set()).add(tu.user_id)

    result = []
    for member in members:
        uid = member.user_id
        member_tasks = [
            t for t in tasks
            if t.user_id == uid or uid in task_user_map.get(t.task_id, set())
        ]
        result.append({
            'user_id': uid,
            'name': users_map.get(uid, f'User {uid}'),
            'role': member.role,
            'total_tasks': len(member_tasks),
            'completed_tasks': sum(1 for t in member_tasks if t.completed),
        })

    status_keys = ['pending', 'in_progress', 'review', 'completed', 'cancelled']
    status_dist = {k: 0 for k in status_keys}
    for t in tasks:
        s = t.status or 'pending'
        if s in status_dist:
            status_dist[s] += 1

    return jsonify({
        'members': sorted(result, key=lambda x: -x['total_tasks']),
        'status_distribution': status_dist,
        'total_tasks': len(tasks),
    }), 200
