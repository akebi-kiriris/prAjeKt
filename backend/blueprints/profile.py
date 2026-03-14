from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from app import db
from models.user import User

profile_bp = Blueprint('profile', __name__)

PROFILE_UPDATE_ALLOWED_FIELDS = {
    'name',
    'username',
    'phone',
    'email',
    'avatar',
    'bio',
    'current_password',
    'new_password',
}

@profile_bp.route('/me', methods=['GET'])
@jwt_required()
def get_profile():
    """取得使用者個人資料"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '使用者不存在'}), 404
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email,
        'phone': user.phone,
        'avatar': user.avatar,
        'bio': user.bio,
        'created_at': user.created_at.isoformat() + 'Z' if user.created_at else None
    }), 200

@profile_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新使用者個人資料"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '使用者不存在'}), 404
    
    data = request.get_json() or {}

    if not isinstance(data, dict):
        return jsonify({'error': '請提供正確的 JSON 物件'}), 400

    unknown_fields = sorted(set(data.keys()) - PROFILE_UPDATE_ALLOWED_FIELDS)
    if unknown_fields:
        return jsonify({'error': f'不允許的欄位: {", ".join(unknown_fields)}'}), 400
    
    # 更新允許的欄位
    if 'name' in data:
        user.name = data['name']
    if 'username' in data:
        # 檢查 username 是否已被使用
        if data['username'] and User.query.filter(User.username == data['username'], User.id != user_id).first():
            return jsonify({'error': '此用戶名已被使用'}), 409
        user.username = data['username'] if data['username'] else None
    if 'phone' in data:
        user.phone = data['phone']
    if 'email' in data:
        user.email = data['email']
    if 'avatar' in data:
        user.avatar = data['avatar']
    if 'bio' in data:
        user.bio = data['bio']
    
    # 處理密碼變更
    if data.get('new_password'):
        if not data.get('current_password'):
            return jsonify({'error': '請提供目前密碼'}), 400
        
        if not check_password_hash(user.password, data['current_password']):
            return jsonify({'error': '目前密碼錯誤'}), 401
        
        user.password = generate_password_hash(data['new_password'])
    
    try:
        db.session.commit()
        return jsonify({'message': '個人資料更新成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/search', methods=['POST'])
@jwt_required()
def search_user():
    """搜尋使用者（透過 username 或 email）"""
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'error': '請提供搜尋條件'}), 400
    
    # 搜尋 username 或 email
    user = User.query.filter(
        (User.username == query) | (User.email == query)
    ).first()
    
    if not user:
        return jsonify({'error': '找不到使用者'}), 404
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email
    }), 200


@profile_bp.route('/chart-stats', methods=['GET'])
@jwt_required()
def get_chart_stats():
    """取得個人數據分析圖表資料"""
    from datetime import datetime, timedelta
    from sqlalchemy import or_
    from models.task import Task
    from models.task_user import TaskUser
    from models.timeline_user import TimelineUser
    from models.timeline import Timeline

    user_id = int(get_jwt_identity())
    today = datetime.utcnow().date()

    # 取得使用者所在的 timeline IDs
    timeline_ids = [tu.timeline_id for tu
                    in TimelineUser.query.filter_by(user_id=user_id).all()]
    # 取得直接指派的任務 IDs
    direct_task_ids = [tu.task_id for tu
                       in TaskUser.query.filter_by(user_id=user_id).all()]

    # OR 條件：自建 | 直接指派 | timeline 成員
    conditions = [Task.user_id == user_id]
    if direct_task_ids:
        conditions.append(Task.task_id.in_(direct_task_ids))
    if timeline_ids:
        conditions.append(Task.timeline_id.in_(timeline_ids))

    tasks = Task.query.filter(
        Task.deleted_at.is_(None),
        or_(*conditions)
    ).all()

    # 1. 狀態分布
    status_keys = ['pending', 'in_progress', 'review', 'completed', 'cancelled']
    status_dist = {k: 0 for k in status_keys}
    for t in tasks:
        s = t.status or 'pending'
        if s in status_dist:
            status_dist[s] += 1

    # 2. 近 30 天完成趨勢（以 updated_at 且 completed=True 近似）
    daily = {}
    for i in range(30):
        d = (today - timedelta(days=29 - i)).isoformat()
        daily[d] = 0
    for t in tasks:
        if t.completed and t.updated_at:
            d = t.updated_at.date().isoformat()
            if d in daily:
                daily[d] += 1
    daily_completions = [{'date': k, 'count': v} for k, v in sorted(daily.items())]

    # 3. 各專案任務量（取前 8）
    if timeline_ids:
        timelines_map = {tl.id: tl.name for tl in Timeline.query.filter(
            Timeline.id.in_(timeline_ids),
            Timeline.deleted_at.is_(None)
        ).all()}
    else:
        timelines_map = {}

    project_counts = {}
    for t in tasks:
        if t.timeline_id and t.timeline_id in timelines_map:
            tid = t.timeline_id
            if tid not in project_counts:
                project_counts[tid] = {'name': timelines_map[tid], 'count': 0}
            project_counts[tid]['count'] += 1

    tasks_by_project = sorted(
        list(project_counts.values()),
        key=lambda x: -x['count']
    )[:8]

    return jsonify({
        'status_distribution': status_dist,
        'daily_completions': daily_completions,
        'tasks_by_project': tasks_by_project,
    }), 200
