from functools import wraps
from datetime import datetime, timedelta, timezone
import json
import os

from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from models import db
from models.notification import Notification
from models.task import Task
from models.task_user import TaskUser
from models.timeline import Timeline
from models.timeline_user import TimelineUser
from models.user import User
from chains import generate_tasks, get_default_llm
from repositories.timeline_repository import (
    get_active_tasks_by_timeline_id,
    get_active_tasks_by_timeline_id_ordered_end_date,
    get_active_timeline_by_id,
    get_active_timelines_by_ids,
    get_task_users_by_task_ids,
    get_timeline_member,
    get_timeline_members,
    get_timeline_memberships_for_user,
    get_timeline_memberships_for_user_ordered_desc,
    get_user_by_email,
    get_user_by_id,
    get_users_by_ids,
)

TIMELINE_UPDATE_ALLOWED_FIELDS = {'name', 'start_date', 'end_date', 'remark'}


class TimelineAIGenerationError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


class TimelineOperationError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def find_unknown_fields(payload, allowed_fields):
    return sorted(set(payload.keys()) - allowed_fields)


def get_user_timeline_role(user_id, timeline_id):
    """查詢使用者在某專案的角色。"""
    member = TimelineUser.query.filter_by(timeline_id=timeline_id, user_id=user_id).first()
    return member.role if member is not None else None


def get_task_access(user_id, task):
    """查詢使用者對某任務的存取權限（支援 timeline 任務與獨立任務）。"""
    if task.timeline_id:
        role = get_user_timeline_role(user_id, task.timeline_id)
        if role is not None:
            return role

    member = TaskUser.query.filter_by(task_id=task.task_id, user_id=user_id).first()
    if member:
        return member.role

    if task.user_id == user_id:
        return 0

    return None


def require_timeline_role(required_role='member'):
    """Decorator：檢查當前使用者在專案中的角色。"""

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_id = int(get_jwt_identity())
            timeline_id = kwargs.get('timeline_id')
            role = get_user_timeline_role(user_id, timeline_id)
            if role is None:
                return jsonify({'error': '你不是此專案成員'}), 403
            if required_role == 'owner' and role != 0:
                return jsonify({'error': '只有負責人可執行此操作'}), 403
            return f(*args, **kwargs)

        return wrapper

    return decorator


def timeline_list_item_to_dict(timeline, role, total_tasks, completed_tasks):
    return {
        'id': timeline.id,
        'name': timeline.name,
        'startDate': timeline.start_date.isoformat() + 'Z' if timeline.start_date else None,
        'endDate': timeline.end_date.isoformat() + 'Z' if timeline.end_date else None,
        'remark': timeline.remark,
        'role': role,
        'totalTasks': total_tasks,
        'completedTasks': completed_tasks,
    }


def timeline_task_item_to_dict(task, assignee_name, assistant_list):
    return {
        'task_id': task.task_id,
        'name': task.name,
        'assignee': assignee_name,
        'assistant': assistant_list,
        'start_date': task.start_date.isoformat() + 'Z' if task.start_date else None,
        'end_date': task.end_date.isoformat() + 'Z' if task.end_date else None,
        'completed': task.completed,
        'timeline_id': task.timeline_id,
        'remark': task.task_remark,
        'isWork': task.isWork,
        'priority': task.priority,
        'status': task.status,
        'tags': task.tags,
    }


def timeline_member_item_to_dict(timeline_member, user):
    return {
        'user_id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email,
        'role': timeline_member.role,
    }


def _build_existing_tasks_info(timeline_id):
    existing_tasks = (
        Task.query.filter_by(timeline_id=timeline_id)
        .filter(Task.deleted_at.is_(None))
        .all()
    )

    existing_tasks_info = []
    for task in existing_tasks:
        estimated_days = 3
        if task.start_date and task.end_date:
            estimated_days = (task.end_date - task.start_date).days

        existing_tasks_info.append(
            {
                'task_id': task.task_id,
                'name': task.name,
                'priority': task.priority,
                'estimated_days': estimated_days,
                'task_remark': task.task_remark or '',
                'isExisting': True,
            }
        )

    return existing_tasks_info


def _build_ai_task_prompt(project_name, description, existing_tasks_info):
    existing_tasks_text = ''
    if existing_tasks_info:
        existing_tasks_text = '\n\n現有任務：\n'
        for idx, task in enumerate(existing_tasks_info, 1):
            existing_tasks_text += (
                f"{idx}. {task['name']} (優先級:{task['priority']}, "
                f"預估:{task['estimated_days']}天)\n"
            )

    safe_description = description if isinstance(description, str) and description.strip() else '無'

    return f"""你是一個專業的專案管理助手。請根據以下專案資訊，為使用者生成合理的任務清單。

                專案名稱: {project_name}
                專案描述: {safe_description}{existing_tasks_text}

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


def _normalize_generated_tasks(generated_tasks, timeline_id):
    if not isinstance(generated_tasks, list):
        raise TimelineAIGenerationError('invalid_payload', 'AI 回傳格式錯誤')

    normalized_tasks = []
    for task in generated_tasks:
        if not isinstance(task, dict):
            raise TimelineAIGenerationError('invalid_payload', 'AI 回傳格式錯誤')

        normalized = {
            'timeline_id': timeline_id,
            'status': 'pending',
            'completed': False,
            'isExisting': False,
            'name': task.get('name', '未命名任務'),
            'priority': task.get('priority', 2),
            'estimated_days': task.get('estimated_days', 3),
            'task_remark': task.get('task_remark', ''),
        }
        normalized_tasks.append(normalized)

    return normalized_tasks


def generate_timeline_tasks_with_ai(timeline_id, project_name, description=''):
    existing_tasks_info = _build_existing_tasks_info(timeline_id)

    prompt = _build_ai_task_prompt(project_name, description, existing_tasks_info)

    try:
        llm = get_default_llm(provider="google-generativeai")
        parsed = generate_tasks(
            llm=llm,
            project_name=project_name,
            project_description=description if isinstance(description, str) else "",
            user_input=prompt,
            user_name="timeline_member",
        )
    except (RuntimeError, ValueError) as exc:
        error_str = str(exc)
        if "GOOGLE_API_KEY" in error_str:
            raise TimelineAIGenerationError('missing_api_key', 'AI 服務配置不完整') from exc
        raise TimelineAIGenerationError('generation_failed', 'AI 生成失敗，請稍後再試') from exc

    generated_tasks = _normalize_generated_tasks(parsed, timeline_id)
    all_tasks = existing_tasks_info + generated_tasks

    return {
        'message': f'現有 {len(existing_tasks_info)} 個任務，AI 生成 {len(generated_tasks)} 個新任務',
        'tasks': all_tasks,
        'existingCount': len(existing_tasks_info),
        'generatedCount': len(generated_tasks),
    }


def _utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_active_timeline_or_404(timeline_id):
    timeline = get_active_timeline_by_id(timeline_id)
    if not timeline:
        raise TimelineOperationError('找不到該專案', 404)
    return timeline


def list_timeline_items_for_user(user_id):
    memberships = get_timeline_memberships_for_user_ordered_desc(user_id)
    result = []
    for timeline, role in memberships:
        tasks = get_active_tasks_by_timeline_id(timeline.id)
        total_tasks = len(tasks)
        completed_tasks = len([task for task in tasks if task.completed])
        result.append(timeline_list_item_to_dict(timeline, role, total_tasks, completed_tasks))
    return result


def create_timeline_for_user(user_id, data):
    name = data.get('name')
    start_date_raw = data.get('start_date', '')
    end_date_raw = data.get('end_date', '')
    remark = data.get('remark', '')

    if not isinstance(name, str) or not name.strip():
        raise TimelineOperationError('請提供專案名稱（字串）', 400)
    if not isinstance(start_date_raw, str):
        raise TimelineOperationError('開始日期必須是字串', 400)
    if not isinstance(end_date_raw, str):
        raise TimelineOperationError('結束日期必須是字串', 400)

    start_date = None
    if start_date_raw.strip():
        try:
            start_date = datetime.fromisoformat(start_date_raw)
        except ValueError:
            raise TimelineOperationError('開始日期格式錯誤，請用 YYYY-MM-DD', 400)

    end_date = None
    if end_date_raw.strip():
        try:
            end_date = datetime.fromisoformat(end_date_raw)
        except ValueError:
            raise TimelineOperationError('結束日期格式錯誤，請用 YYYY-MM-DD', 400)

    new_timeline = Timeline(
        user_id=user_id,
        name=name.strip(),
        start_date=start_date,
        end_date=end_date,
        remark=remark,
    )

    try:
        db.session.add(new_timeline)
        db.session.flush()
        db.session.add(TimelineUser(timeline_id=new_timeline.id, user_id=user_id, role=0))
        db.session.commit()
        return new_timeline.id
    except Exception as exc:
        db.session.rollback()
        raise TimelineOperationError('專案新增失敗，請稍後再試', 500) from exc


def update_timeline_for_member(timeline_id, data):
    timeline = get_active_timeline_or_404(timeline_id)

    unknown_fields = find_unknown_fields(data, TIMELINE_UPDATE_ALLOWED_FIELDS)
    if unknown_fields:
        raise TimelineOperationError(f'不允許的欄位: {", ".join(unknown_fields)}', 400)

    if 'name' in data:
        if not data['name'] or not data['name'].strip():
            raise TimelineOperationError('專案名稱不可為空', 400)
        timeline.name = data['name'].strip()

    if 'start_date' in data:
        start_date_value = data['start_date']
        if start_date_value and isinstance(start_date_value, str) and start_date_value.strip():
            try:
                timeline.start_date = datetime.fromisoformat(start_date_value)
            except ValueError:
                raise TimelineOperationError('開始日期格式錯誤', 400)
        elif start_date_value in (None, ''):
            timeline.start_date = None
        else:
            raise TimelineOperationError('開始日期格式錯誤', 400)

    if 'end_date' in data:
        end_date_value = data['end_date']
        if end_date_value and isinstance(end_date_value, str) and end_date_value.strip():
            try:
                timeline.end_date = datetime.fromisoformat(end_date_value)
            except ValueError:
                raise TimelineOperationError('結束日期格式錯誤', 400)
        elif end_date_value in (None, ''):
            timeline.end_date = None
        else:
            raise TimelineOperationError('結束日期格式錯誤', 400)

    if 'remark' in data:
        timeline.remark = data['remark']

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise TimelineOperationError('專案更新失敗，請稍後再試', 500) from exc


def soft_delete_timeline_for_owner(timeline_id):
    timeline = get_active_timeline_or_404(timeline_id)

    try:
        deleted_at = _utcnow_naive()
        timeline.deleted_at = deleted_at
        Task.query.filter_by(timeline_id=timeline_id).update({'deleted_at': deleted_at})
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise TimelineOperationError('專案刪除失敗，請稍後再試', 500) from exc


def list_timeline_tasks_detail(timeline_id):
    tasks = get_active_tasks_by_timeline_id_ordered_end_date(timeline_id)
    task_ids = [task.task_id for task in tasks]
    task_users = get_task_users_by_task_ids(task_ids)

    users_map = {
        user.id: user
        for user in get_users_by_ids({task_user.user_id for task_user in task_users})
    }

    task_user_map = {}
    for task_user in task_users:
        task_user_map.setdefault(task_user.task_id, []).append(task_user)

    result = []
    for task in tasks:
        assignee_name = None
        assistant_list = []
        for task_user in task_user_map.get(task.task_id, []):
            user = users_map.get(task_user.user_id)
            if not user:
                continue
            if task_user.role == 0 and assignee_name is None:
                assignee_name = user.name
            elif task_user.role == 1:
                assistant_list.append(user.name)

        result.append(timeline_task_item_to_dict(task, assignee_name, assistant_list))

    return result


def update_timeline_remark_for_member(timeline_id, remark):
    timeline = get_active_timeline_or_404(timeline_id)

    if not isinstance(remark, str):
        raise TimelineOperationError('備註必須是字串', 400)

    try:
        timeline.remark = remark
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise TimelineOperationError('備註更新失敗，請稍後再試', 500) from exc


def search_timeline_user_by_email(email):
    if not email:
        raise TimelineOperationError('請提供 Email', 400)

    user = get_user_by_email(email)
    if not user:
        raise TimelineOperationError('找不到該使用者', 404)

    return user


def list_timeline_members_payload(timeline_id):
    members = get_timeline_members(timeline_id)
    users_map = {user.id: user for user in get_users_by_ids([member.user_id for member in members])}

    result = []
    for member in members:
        user = users_map.get(member.user_id)
        if user:
            result.append(timeline_member_item_to_dict(member, user))
    return result


def add_timeline_member_for_owner(timeline_id, invited_user_id, role, actor_user_id):
    if not invited_user_id:
        raise TimelineOperationError('請提供使用者 ID', 400)

    try:
        member = TimelineUser(timeline_id=timeline_id, user_id=invited_user_id, role=role)
        db.session.add(member)

        actor = get_user_by_id(actor_user_id)
        timeline = get_active_timeline_by_id(timeline_id)
        if timeline is None:
            timeline = db.session.get(Timeline, timeline_id)

        actor_name = actor.name if actor else '某人'
        timeline_name = timeline.name if timeline else '專案'

        notif = Notification(
            user_id=invited_user_id,
            type='timeline_invited',
            title=f'你被邀請加入專案「{timeline_name}」',
            content=f'{actor_name} 邀請你加入「{timeline_name}」',
            link='/timelines',
        )
        db.session.add(notif)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise TimelineOperationError('成員新增失敗，請稍後再試', 500) from exc


def remove_timeline_member_for_owner(timeline_id, member_user_id, operator_user_id):
    if member_user_id == operator_user_id:
        raise TimelineOperationError('不能將自己移出專案', 400)

    member = get_timeline_member(timeline_id, member_user_id)
    if not member or member.role == 0:
        raise TimelineOperationError('找不到該成員，或無法移除負責人', 404)

    try:
        db.session.delete(member)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise TimelineOperationError('成員移除失敗，請稍後再試', 500) from exc


def batch_create_tasks_for_timeline(timeline_id, user_id, task_payloads):
    timeline = get_active_timeline_or_404(timeline_id)

    if not isinstance(task_payloads, list) or len(task_payloads) == 0:
        raise TimelineOperationError('請提供至少一個任務', 400)

    try:
        all_existing_task_ids = [task.task_id for task in get_active_tasks_by_timeline_id(timeline_id)]
        selected_existing_task_ids = [
            task['task_id']
            for task in task_payloads
            if task.get('isExisting') and task.get('task_id')
        ]

        tasks_to_delete = set(all_existing_task_ids) - set(selected_existing_task_ids)
        if tasks_to_delete:
            Task.query.filter(Task.task_id.in_(tasks_to_delete)).update(
                {'deleted_at': _utcnow_naive()},
                synchronize_session=False,
            )

        created_tasks = []
        start_date = timeline.start_date or datetime.now()
        current_date = start_date

        for task_data in task_payloads:
            if task_data.get('isExisting'):
                continue

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
                isWork=1,
            )
            db.session.add(new_task)
            created_tasks.append(new_task.name)
            current_date = end_date

        db.session.commit()
        return {
            'message': (
                f'保留 {len(selected_existing_task_ids)} 個舊任務，'
                f'刪除 {len(tasks_to_delete)} 個舊任務，新增 {len(created_tasks)} 個任務'
            ),
            'kept': len(selected_existing_task_ids),
            'deleted': len(tasks_to_delete),
            'created': len(created_tasks),
        }
    except Exception as exc:
        db.session.rollback()
        raise TimelineOperationError('批次建立任務失敗，請稍後再試', 500) from exc


def list_upcoming_timelines_for_user(user_id):
    today = datetime.now(timezone.utc).date()
    threshold = today + timedelta(days=3)

    memberships = get_timeline_memberships_for_user(user_id)
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
            result.append(
                {
                    'id': timeline.id,
                    'name': timeline.name,
                    'end_date': end.isoformat(),
                    'role': role,
                    'is_overdue': end < today,
                    'type': 'timeline',
                }
            )

    return result


def build_timeline_member_stats_payload(timeline_id):
    members = get_timeline_members(timeline_id)
    member_ids = [member.user_id for member in members]
    users_map = {user.id: user.name for user in get_users_by_ids(member_ids)}

    tasks = get_active_tasks_by_timeline_id(timeline_id)
    task_ids = [task.task_id for task in tasks]

    task_user_map = {}
    for task_user in get_task_users_by_task_ids(task_ids):
        task_user_map.setdefault(task_user.task_id, set()).add(task_user.user_id)

    members_payload = []
    for member in members:
        uid = member.user_id
        member_tasks = [
            task
            for task in tasks
            if task.user_id == uid or uid in task_user_map.get(task.task_id, set())
        ]
        members_payload.append(
            {
                'user_id': uid,
                'name': users_map.get(uid, f'User {uid}'),
                'role': member.role,
                'total_tasks': len(member_tasks),
                'completed_tasks': sum(1 for task in member_tasks if task.completed),
            }
        )

    status_keys = ['pending', 'in_progress', 'review', 'completed', 'cancelled']
    status_dist = {key: 0 for key in status_keys}
    for task in tasks:
        status = task.status or 'pending'
        if status in status_dist:
            status_dist[status] += 1

    return {
        'members': sorted(members_payload, key=lambda item: -item['total_tasks']),
        'status_distribution': status_dist,
        'total_tasks': len(tasks),
    }
