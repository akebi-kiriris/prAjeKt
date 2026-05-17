from datetime import datetime, timedelta, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from repositories.profile_repository import (
    get_user_by_email_excluding_id,
    get_user_by_id,
    get_user_by_username_excluding_id,
    list_active_tasks_for_user_scope,
    list_active_timelines_by_ids,
    list_direct_task_ids_for_user,
    list_timeline_ids_for_user,
    search_user_by_username_or_email,
)
from services.transactions import transaction


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


class ProfileOperationError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def find_unknown_fields(payload, allowed_fields):
    return sorted(set(payload.keys()) - allowed_fields)


def profile_to_dict(user):
    return {
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email,
        'phone': user.phone,
        'avatar': user.avatar,
        'bio': user.bio,
        'created_at': user.created_at.isoformat() + 'Z' if user.created_at else None,
    }


def search_user_to_dict(user):
    return {
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email,
    }


def get_profile_user_or_404(user_id):
    user = get_user_by_id(user_id)
    if not user:
        raise ProfileOperationError('使用者不存在', 404)
    return user


def update_profile_for_user(user_id, data):
    if not isinstance(data, dict):
        raise ProfileOperationError('請提供正確的 JSON 物件', 400)

    user = get_profile_user_or_404(user_id)

    unknown_fields = find_unknown_fields(data, PROFILE_UPDATE_ALLOWED_FIELDS)
    if unknown_fields:
        raise ProfileOperationError(f'不允許的欄位: {", ".join(unknown_fields)}', 400)

    if 'name' in data:
        user.name = data['name']

    if 'username' in data:
        normalized_username = (
            data['username'].strip()
            if isinstance(data['username'], str) and data['username'].strip()
            else None
        )
        if normalized_username and get_user_by_username_excluding_id(normalized_username, user_id):
            raise ProfileOperationError('此用戶名已被使用', 409)
        user.username = normalized_username

    if 'phone' in data:
        user.phone = data['phone']

    if 'email' in data:
        if not isinstance(data['email'], str) or not data['email'].strip():
            raise ProfileOperationError('email 必須是非空字串', 400)
        normalized_email = data['email'].strip().lower()
        if get_user_by_email_excluding_id(normalized_email, user_id):
            raise ProfileOperationError('此 email 已被使用', 409)
        user.email = normalized_email

    if 'avatar' in data:
        user.avatar = data['avatar']

    if 'bio' in data:
        user.bio = data['bio']

    if data.get('new_password'):
        if not data.get('current_password'):
            raise ProfileOperationError('請提供目前密碼', 400)
        if not check_password_hash(user.password, data['current_password']):
            raise ProfileOperationError('目前密碼錯誤', 401)
        user.password = generate_password_hash(data['new_password'])

    with transaction(ProfileOperationError, '更新個人資料失敗，請稍後再試'):
        pass


def search_user_by_query(query):
    normalized_query = query.strip() if isinstance(query, str) else ''
    if not normalized_query:
        raise ProfileOperationError('請提供搜尋條件', 400)

    user = search_user_by_username_or_email(normalized_query)

    if not user:
        raise ProfileOperationError('找不到使用者', 404)

    return user


def build_chart_stats_for_user(user_id):
    today = datetime.now(timezone.utc).date()

    timeline_ids = list_timeline_ids_for_user(user_id)
    direct_task_ids = list_direct_task_ids_for_user(user_id)
    tasks = list_active_tasks_for_user_scope(user_id, direct_task_ids, timeline_ids)

    status_keys = ['pending', 'in_progress', 'review', 'completed', 'cancelled']
    status_dist = {key: 0 for key in status_keys}
    for task in tasks:
        status = task.status or 'pending'
        if status in status_dist:
            status_dist[status] += 1

    daily = {}
    for i in range(30):
        date_key = (today - timedelta(days=29 - i)).isoformat()
        daily[date_key] = 0

    for task in tasks:
        if task.completed and task.updated_at:
            date_key = task.updated_at.date().isoformat()
            if date_key in daily:
                daily[date_key] += 1

    daily_completions = [{'date': key, 'count': value} for key, value in sorted(daily.items())]

    if timeline_ids:
        timelines_map = {
            timeline.id: timeline.name
            for timeline in list_active_timelines_by_ids(timeline_ids)
        }
    else:
        timelines_map = {}

    project_counts = {}
    for task in tasks:
        if task.timeline_id and task.timeline_id in timelines_map:
            timeline_id = task.timeline_id
            if timeline_id not in project_counts:
                project_counts[timeline_id] = {'name': timelines_map[timeline_id], 'count': 0}
            project_counts[timeline_id]['count'] += 1

    tasks_by_project = sorted(project_counts.values(), key=lambda item: -item['count'])[:8]

    return {
        'status_distribution': status_dist,
        'daily_completions': daily_completions,
        'tasks_by_project': tasks_by_project,
    }
