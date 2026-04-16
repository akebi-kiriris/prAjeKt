from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
import os

from models import db
from models.notification import Notification
from models.task import Task
from models.timeline import Timeline
from models.timeline_user import TimelineUser
from chains import (
    get_default_llm,
    generate_timeline_tasks_from_context,
    generate_weekly_report_summary,
    generate_conflict_suggestion,
)
from repositories.timeline_repository import (
    get_active_tasks_by_timeline_id,
    get_active_tasks_by_timeline_id_ordered_end_date,
    get_active_timeline_by_id,
    get_active_timelines_by_ids,
    get_task_user_membership,
    get_task_users_by_task_ids,
    get_timeline_by_id,
    get_timeline_member,
    get_timeline_role,
    get_timeline_members,
    get_timeline_memberships_for_user,
    get_timeline_memberships_for_user_ordered_desc,
    list_active_tasks_for_assignee,
    list_cross_project_active_tasks_for_assignee,
    list_recent_task_comments_for_timeline_period,
    list_task_ids_by_assignee_user_id,
    list_task_ids_by_assignee_user_id_within,
    soft_delete_tasks_by_ids,
    soft_delete_tasks_by_timeline_id,
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
    return get_timeline_role(timeline_id, user_id)


def get_task_access(user_id, task):
    """查詢使用者對某任務的存取權限（支援 timeline 任務與獨立任務）。"""
    if task.timeline_id:
        role = get_user_timeline_role(user_id, task.timeline_id)
        if role is not None:
            return role

    member = get_task_user_membership(task.task_id, user_id)
    if member:
        return member.role

    if task.user_id == user_id:
        return 0

    return None


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
        'completed_at': task.completed_at.isoformat() + 'Z' if task.completed_at else None,
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
    existing_tasks = get_active_tasks_by_timeline_id(timeline_id)

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

    try:
        provider = os.getenv('LLM_PROVIDER', 'google-generativeai')
        llm = get_default_llm(provider=provider)
        parsed = generate_timeline_tasks_from_context(
            llm=llm,
            project_name=project_name,
            project_description=description,
            existing_tasks_info=existing_tasks_info,
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
        soft_delete_tasks_by_timeline_id(timeline_id, deleted_at)
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


def _iso_datetime_with_z(value):
    return value.isoformat() + 'Z' if value else None


def _to_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_task_priority(value, default=2):
    parsed = _to_int(value)
    if parsed in (1, 2, 3):
        return parsed
    return default


def _priority_label(priority):
    return {
        1: '高',
        2: '中',
        3: '低',
    }.get(priority, '中')


def _parse_date_input(value, field_name):
    if value in (None, ''):
        return None

    if not isinstance(value, str):
        raise TimelineOperationError(f'{field_name} 格式錯誤，請使用 YYYY-MM-DD', 400)

    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        raise TimelineOperationError(f'{field_name} 格式錯誤，請使用 YYYY-MM-DD', 400)


def _normalize_report_period(start_date_raw, end_date_raw):
    today = datetime.now(timezone.utc).date()

    start_date = _parse_date_input(start_date_raw, 'start_date')
    end_date = _parse_date_input(end_date_raw, 'end_date')

    if start_date is None and end_date is None:
        end_date = today
        start_date = today - timedelta(days=6)
    elif start_date is None:
        start_date = end_date - timedelta(days=6)
    elif end_date is None:
        end_date = start_date + timedelta(days=6)

    if start_date > end_date:
        raise TimelineOperationError('start_date 不可晚於 end_date', 400)

    return start_date, end_date


def _resolve_task_window(task):
    start_date = task.start_date.date() if task.start_date else None
    end_date = task.end_date.date() if task.end_date else None

    if start_date is None and end_date is None:
        return None, None
    if start_date is None:
        start_date = end_date
    if end_date is None:
        end_date = start_date

    return start_date, end_date


def _resolve_task_completed_date(task):
    if task.completed_at:
        return task.completed_at.date()

    if task.completed and task.updated_at:
        return task.updated_at.date()

    return None


def _parse_task_tags(raw_tags):
    if not isinstance(raw_tags, str):
        return []

    return [tag.strip() for tag in raw_tags.split(',') if tag.strip()]


def build_weekly_report_for_timeline(timeline_id, start_date_raw=None, end_date_raw=None):
    timeline = get_active_timeline_or_404(timeline_id)
    start_date, end_date = _normalize_report_period(start_date_raw, end_date_raw)

    tasks = get_active_tasks_by_timeline_id(timeline_id)
    owner_map = {user.id: user.name for user in get_users_by_ids({task.user_id for task in tasks})}

    completed_tasks = []
    risk_items = []

    for task in tasks:
        completed_date = _resolve_task_completed_date(task)
        due_date = task.end_date.date() if task.end_date else None

        if completed_date and start_date <= completed_date <= end_date:
            completed_tasks.append(
                {
                    'task_id': task.task_id,
                    'name': task.name,
                    'completed_at': _iso_datetime_with_z(task.completed_at or task.updated_at),
                    'due_date': due_date.isoformat() if due_date else None,
                    'is_late': bool(due_date and completed_date > due_date),
                    'owner_name': owner_map.get(task.user_id),
                }
            )

        if task.completed or not due_date:
            continue

        reason = None
        days_overdue = 0
        days_remaining = None

        if due_date < start_date:
            reason = '已逾期'
            days_overdue = (start_date - due_date).days
        elif due_date <= end_date:
            reason = '本期到期'
            days_remaining = (due_date - start_date).days

        if reason:
            risk_items.append(
                {
                    'task_id': task.task_id,
                    'name': task.name,
                    'status': task.status,
                    'due_date': due_date.isoformat(),
                    'reason': reason,
                    'days_overdue': days_overdue,
                    'days_remaining': days_remaining,
                }
            )

    period_start_dt = datetime.combine(start_date, datetime.min.time())
    period_end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time())

    recent_comments = list_recent_task_comments_for_timeline_period(
        timeline_id,
        period_start_dt,
        period_end_dt,
        limit=20,
    )

    task_name_map = {task.task_id: task.name for task in tasks}
    recent_comments_payload = [
        {
            'comment_id': comment.comment_id,
            'task_id': comment.task_id,
            'task_name': task_name_map.get(comment.task_id),
            'user_id': comment.user_id,
            'message': comment.task_message,
            'created_at': _iso_datetime_with_z(comment.created_at),
        }
        for comment in recent_comments
    ]

    pending_tasks = [task for task in tasks if not task.completed]
    pending_tasks.sort(key=lambda task: (task.end_date is None, task.end_date or datetime.max))

    next_actions = []
    for task in pending_tasks[:3]:
        due_date = task.end_date.date().isoformat() if task.end_date else '未設定'
        next_actions.append(f'優先處理「{task.name}」（截止：{due_date}）')

    total_tasks = len(tasks)
    completion_rate = round((len(completed_tasks) / total_tasks) * 100, 1) if total_tasks else 0.0

    due_tasks_in_period = [
        task
        for task in tasks
        if task.end_date and start_date <= task.end_date.date() <= end_date
    ]
    weekly_goal_total = len(due_tasks_in_period)
    weekly_goal_completed = 0
    for task in due_tasks_in_period:
        completed_date = _resolve_task_completed_date(task)
        if completed_date and completed_date <= end_date:
            weekly_goal_completed += 1

    weekly_goal_completion_rate = (
        round((weekly_goal_completed / weekly_goal_total) * 100, 1)
        if weekly_goal_total
        else completion_rate
    )

    period_days = max((end_date - start_date).days + 1, 1)
    previous_end_date = start_date - timedelta(days=1)
    previous_start_date = previous_end_date - timedelta(days=period_days - 1)
    previous_completed_count = 0
    for task in tasks:
        completed_date = _resolve_task_completed_date(task)
        if completed_date and previous_start_date <= completed_date <= previous_end_date:
            previous_completed_count += 1

    progress_delta = len(completed_tasks) - previous_completed_count

    if weekly_goal_completion_rate >= 80 and len(risk_items) <= 1:
        progress_signal = '進度領先'
    elif weekly_goal_completion_rate >= 60 and len(risk_items) <= 3:
        progress_signal = '進度穩定'
    else:
        progress_signal = '進度落後'

    owner_counter = Counter(item.get('owner_name') or '未指定' for item in completed_tasks)
    top_owner_name, top_owner_count = owner_counter.most_common(1)[0] if owner_counter else ('未明顯集中', 0)
    top_owner_text = (
        f'{top_owner_name}（完成 {top_owner_count} 項）'
        if owner_counter
        else '本期無明顯貢獻者'
    )

    completed_tag_counter = Counter()
    for task in tasks:
        completed_date = _resolve_task_completed_date(task)
        if not completed_date or not (start_date <= completed_date <= end_date):
            continue
        completed_tag_counter.update(_parse_task_tags(task.tags))

    top_tags = [tag for tag, _count in completed_tag_counter.most_common(3)]
    top_tags_text = '、'.join(top_tags) if top_tags else '尚未形成明顯模組重點'

    block_keywords = ('卡住', '阻塞', '等待', '延遲', '風險', 'blocked', 'issue')
    blocking_comment_count = 0
    for comment in recent_comments:
        message = str(comment.task_message or '')
        if any(keyword in message for keyword in block_keywords):
            blocking_comment_count += 1

    # Phase 7.1：使用 chains 層的 LangChain 生成 AI 週報摘要（含目標達成率、趨勢與原因）
    status_text = "\n".join(
        [
            f"專案名稱: {timeline.name}",
            f"週期: {start_date.isoformat()} 至 {end_date.isoformat()}",
            f"本期完成任務: {len(completed_tasks)}",
            f"本期目標任務數(到期): {weekly_goal_total}",
            f"本期目標達成率: {weekly_goal_completion_rate}%",
            f"前一期完成任務數: {previous_completed_count}",
            f"完成趨勢變化: {progress_delta:+d}",
            f"進度判讀: {progress_signal}",
            f"風險項目數: {len(risk_items)}",
            f"留言數: {len(recent_comments_payload)}",
            f"阻塞訊號數: {blocking_comment_count}",
            f"主要推進角色: {top_owner_text}",
            f"主要推進模組: {top_tags_text}",
            f"下一步建議: {'；'.join(next_actions) if next_actions else '目前無明確下一步'}",
        ]
    )

    ai_summary = (
        f"本期目標達成率 {weekly_goal_completion_rate}%（{progress_signal}），"
        f"主要推進動能來自 {top_owner_text}。"
        f"目前風險項目 {len(risk_items)} 項，建議優先處理到期任務並降低阻塞。"
    )
    try:
        provider = os.getenv('LLM_PROVIDER', 'google-generativeai')
        llm = get_default_llm(provider=provider)
        generated = generate_weekly_report_summary(llm=llm, status_text=status_text)
        if generated:
            ai_summary = generated
    except Exception:
        pass

    return {
        'message': '週報生成成功',
        'timeline_id': timeline.id,
        'timeline_name': timeline.name,
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        },
        'overview': {
            'total_tasks': total_tasks,
            'completed_tasks': len(completed_tasks),
            'completion_rate': completion_rate,
            'at_risk_tasks': len(risk_items),
            'comment_count': len(recent_comments_payload),
        },
        'completed_tasks': completed_tasks,
        'risk_items': risk_items,
        'recent_comments': recent_comments_payload,
        'next_actions': next_actions,
        'ai_summary': ai_summary,
        'analysis': {
            'weekly_goal_total': weekly_goal_total,
            'weekly_goal_completed': weekly_goal_completed,
            'weekly_goal_completion_rate': weekly_goal_completion_rate,
            'previous_completed_tasks': previous_completed_count,
            'progress_delta': progress_delta,
            'progress_signal': progress_signal,
            'top_owner': top_owner_name if owner_counter else None,
            'top_tags': top_tags,
            'blocking_comment_count': blocking_comment_count,
        },
    }


def check_timeline_task_conflicts(timeline_id, payload, actor_user_id):
    if not isinstance(payload, dict):
        raise TimelineOperationError('請提供正確的 JSON 物件', 400)

    timeline = get_active_timeline_or_404(timeline_id)

    end_date = _parse_date_input(payload.get('end_date'), 'end_date')
    if end_date is None:
        raise TimelineOperationError('end_date 為必填，格式請使用 YYYY-MM-DD', 400)

    start_date = _parse_date_input(payload.get('start_date'), 'start_date') or end_date
    if start_date > end_date:
        raise TimelineOperationError('start_date 不可晚於 end_date', 400)

    assignee_user_id = _to_int(payload.get('assignee_user_id')) or actor_user_id
    excluded_task_id = _to_int(payload.get('task_id'))
    task_name = str(payload.get('name') or '').strip() or None
    task_priority = _normalize_task_priority(payload.get('priority'))
    priority_label = _priority_label(task_priority)

    assignee_member = get_timeline_member(timeline_id, assignee_user_id)
    if assignee_member is None:
        raise TimelineOperationError('assignee_user_id 必須是專案成員', 400)

    assignee_user = get_user_by_id(assignee_user_id)
    assignee_name = assignee_user.name if assignee_user else None
    should_mask_task_names = assignee_user_id != actor_user_id

    assignee_task_id_set = set(list_task_ids_by_assignee_user_id(assignee_user_id))

    all_tasks = [task for task in get_active_tasks_by_timeline_id(timeline_id) if not task.completed]
    candidates = [
        task for task in all_tasks if excluded_task_id is None or task.task_id != excluded_task_id
    ]

    candidate_task_ids = [task.task_id for task in candidates]
    assignee_task_ids = set()
    if candidate_task_ids:
        assignee_task_ids = set(
            list_task_ids_by_assignee_user_id_within(assignee_user_id, candidate_task_ids)
        )

    users_map = {
        user.id: user.name
        for user in get_users_by_ids({task.user_id for task in candidates})
    }

    cross_project_tasks = list_cross_project_active_tasks_for_assignee(
        assignee_user_id=assignee_user_id,
        current_timeline_id=timeline_id,
        assignee_task_id_set=assignee_task_id_set,
        excluded_task_id=excluded_task_id,
    )

    cross_timeline_ids = {task.timeline_id for task in cross_project_tasks if task.timeline_id is not None}
    timeline_name_map = {timeline_id: timeline.name}
    if cross_timeline_ids:
        timeline_name_map.update(
            {
                item.id: item.name
                for item in get_active_timelines_by_ids(cross_timeline_ids)
            }
        )

    users_map.update(
        {
            user.id: user.name
            for user in get_users_by_ids({task.user_id for task in cross_project_tasks})
        }
    )

    conflicts = []
    max_conflict_end = None

    for task in candidates:
        existing_start, existing_end = _resolve_task_window(task)
        if existing_start is None or existing_end is None:
            continue

        is_overlapping = start_date <= existing_end and end_date >= existing_start
        if not is_overlapping:
            continue

        same_assignee = (task.user_id == assignee_user_id) or (task.task_id in assignee_task_ids)
        reason = '與同成員既有任務日期重疊' if same_assignee else '與專案內既有任務日期重疊'

        conflicts.append(
            {
                'task_id': task.task_id,
                'name': task.name if not should_mask_task_names else '既有任務（隱私保護）',
                'status': task.status,
                'start_date': existing_start.isoformat(),
                'end_date': existing_end.isoformat(),
                'owner_name': users_map.get(task.user_id),
                'same_assignee': same_assignee,
                'reason': reason,
                'timeline_id': timeline_id,
                'timeline_name': timeline.name,
                'is_cross_project': False,
            }
        )

        if max_conflict_end is None or existing_end > max_conflict_end:
            max_conflict_end = existing_end

    for task in cross_project_tasks:
        existing_start, existing_end = _resolve_task_window(task)
        if existing_start is None or existing_end is None:
            continue

        is_overlapping = start_date <= existing_end and end_date >= existing_start
        if not is_overlapping:
            continue

        conflicts.append(
            {
                'task_id': task.task_id,
                'name': task.name if not should_mask_task_names else '跨專案任務（隱私保護）',
                'status': task.status,
                'start_date': existing_start.isoformat(),
                'end_date': existing_end.isoformat(),
                'owner_name': users_map.get(task.user_id),
                'same_assignee': True,
                'reason': '與該成員其他專案任務撞期',
                'timeline_id': task.timeline_id,
                'timeline_name': timeline_name_map.get(task.timeline_id),
                'is_cross_project': True,
            }
        )

        if max_conflict_end is None or existing_end > max_conflict_end:
            max_conflict_end = existing_end

    assignee_active_tasks = list_active_tasks_for_assignee(
        assignee_user_id=assignee_user_id,
        assignee_task_id_set=assignee_task_id_set,
        excluded_task_id=excluded_task_id,
    )

    overload_threshold = _to_int(os.getenv('ASSIGNEE_DAILY_OVERLOAD_THRESHOLD')) or 3
    daily_existing_counts = defaultdict(int)
    daily_task_names = defaultdict(list)

    for task in assignee_active_tasks:
        existing_start, existing_end = _resolve_task_window(task)
        if existing_start is None or existing_end is None:
            continue

        overlap_start = max(start_date, existing_start)
        overlap_end = min(end_date, existing_end)
        if overlap_start > overlap_end:
            continue

        day_cursor = overlap_start
        while day_cursor <= overlap_end:
            daily_existing_counts[day_cursor] += 1
            if (not should_mask_task_names) and len(daily_task_names[day_cursor]) < 5:
                daily_task_names[day_cursor].append(task.name)
            day_cursor += timedelta(days=1)

    workload_overload_days = []
    day_cursor = start_date
    while day_cursor <= end_date:
        projected_count = daily_existing_counts[day_cursor] + 1
        if projected_count > overload_threshold:
            workload_overload_days.append(
                {
                    'date': day_cursor.isoformat(),
                    'existing_task_count': daily_existing_counts[day_cursor],
                    'projected_task_count': projected_count,
                    'threshold': overload_threshold,
                    'sample_tasks': daily_task_names[day_cursor][:3],
                }
            )
        day_cursor += timedelta(days=1)

    suggestion = None
    suggestion_buffer_days = 1 if task_priority == 3 else 0
    if max_conflict_end is not None:
        duration_days = (end_date - start_date).days
        suggested_start = max_conflict_end + timedelta(days=1 + suggestion_buffer_days)
        suggested_end = suggested_start + timedelta(days=duration_days)
        suggestion = {
            'start_date': suggested_start.isoformat(),
            'end_date': suggested_end.isoformat(),
        }
    elif workload_overload_days:
        duration_days = (end_date - start_date).days
        latest_overload_date = max(
            datetime.fromisoformat(item['date']).date()
            for item in workload_overload_days
        )
        suggested_start = latest_overload_date + timedelta(days=1 + suggestion_buffer_days)
        suggested_end = suggested_start + timedelta(days=duration_days)
        suggestion = {
            'start_date': suggested_start.isoformat(),
            'end_date': suggested_end.isoformat(),
        }

    cross_project_conflict_count = len([item for item in conflicts if item.get('is_cross_project')])
    workload_overload_count = len(workload_overload_days)
    total_signal_count = len(conflicts) + workload_overload_count

    has_conflict = total_signal_count > 0
    assignee_conflict_count = len([item for item in conflicts if item['same_assignee']])

    # Phase 7.1：使用 chains 層的 LangChain 生成 AI 衝突建議
    ai_suggestion_text = ""
    if has_conflict and suggestion:
        cross_conflicts_preview = [
            f"{item['name']}（{item.get('timeline_name') or '未知專案'}）"
            for item in conflicts
            if item.get('is_cross_project')
        ][:3]
        overload_preview = [
            f"{item['date']}（預估 {item['projected_task_count']} 項）"
            for item in workload_overload_days
        ][:3]
        conflict_summary = (
            f"總衝突訊號: {total_signal_count}\n"
            f"新任務優先級: {priority_label}（{task_priority}）\n"
            f"日期衝突: {len(conflicts)}（跨專案: {cross_project_conflict_count}）\n"
            f"同成員衝突: {assignee_conflict_count}\n"
            f"工作量過載日: {workload_overload_count}\n"
            f"跨專案撞期案例: {'；'.join(cross_conflicts_preview) if cross_conflicts_preview else '無'}\n"
            f"過載日期案例: {'；'.join(overload_preview) if overload_preview else '無'}"
        )
        suggestion_range = f"{suggestion['start_date']} 至 {suggestion['end_date']}"
        try:
            provider = os.getenv('LLM_PROVIDER', 'google-generativeai')
            llm = get_default_llm(provider=provider)
            ai_suggestion_text = generate_conflict_suggestion(
                llm=llm,
                conflict_text=conflict_summary,
                suggestion_date_range=suggestion_range,
            )
        except Exception:
            ai_suggestion_text = ""

    message = '未偵測到排程衝突'
    if has_conflict:
        message = f'偵測到 {len(conflicts)} 個日期衝突'
        if workload_overload_count:
            message += f'，另有 {workload_overload_count} 天工作量過載'

    return {
        'message': message,
        'timeline_id': timeline_id,
        'task_name': task_name,
        'priority': task_priority,
        'priority_label': priority_label,
        'has_conflict': has_conflict,
        'conflict_count': total_signal_count,
        'assignee_user_id': assignee_user_id,
        'assignee_name': assignee_name,
        'is_task_name_redacted': should_mask_task_names,
        'assignee_conflict_count': assignee_conflict_count,
        'project_conflict_count': len(conflicts) - assignee_conflict_count,
        'cross_project_conflict_count': cross_project_conflict_count,
        'workload_overload_count': workload_overload_count,
        'workload_overload_days': workload_overload_days,
        'conflicts': conflicts,
        'suggestion': suggestion if has_conflict else None,
        'ai_suggestion': ai_suggestion_text,
    }


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
            timeline = get_timeline_by_id(timeline_id)

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
            soft_delete_tasks_by_ids(list(tasks_to_delete), _utcnow_naive())

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
