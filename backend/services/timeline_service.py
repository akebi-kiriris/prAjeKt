from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import hashlib
import os
import time
from typing import Any

from pydantic import ValidationError

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
from services.critical_path_service import build_critical_path_analysis_payload
from services.transactions import transaction
from repositories.timeline_repository import (
    build_timeline_entity,
    build_timeline_member_entity,
    build_timeline_task_entity,
    get_active_incomplete_tasks_by_timeline_id,
    get_active_tasks_by_timeline_id,
    get_active_tasks_by_timeline_ids,
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
    soft_delete_tasks_by_ids,
    soft_delete_tasks_by_timeline_id,
    get_user_by_email,
    get_user_by_id,
    get_users_by_ids,
)
from repositories.session_repository import add_entity, delete_entity, flush_session
from contracts.response_helpers import build_response_payload
from contracts.timeline_contracts import (
    ConflictCheckInput,
    TimelineConflictCheckResponse,
    TimelineBatchCreateTasksResponse,
    TimelineCreateInput,
    TimelineBatchCreateTasksInput,
    TimelineGenerateTasksResponse,
    TimelineListItemResponse,
    TimelineMemberResponse,
    TimelineMemberStatsResponse,
    TimelineRiskAnalysisResponse,
    TimelineRiskNotificationResponse,
    TimelineTaskItemResponse,
    TimelineUpdateInput,
    UpcomingTimelineResponse,
    WeeklyReportInput,
    WeeklyReportResponse,
)

TIMELINE_UPDATE_ALLOWED_FIELDS = {'name', 'start_date', 'end_date', 'remark'}
WEEKLY_REPORT_AI_TIMEOUT_SEC = float(os.getenv('WEEKLY_REPORT_AI_TIMEOUT_SEC', '35'))
WEEKLY_REPORT_AI_CACHE_TTL_SEC = int(os.getenv('WEEKLY_REPORT_AI_CACHE_TTL_SEC', '300'))
_WEEKLY_REPORT_AI_SUMMARY_CACHE = {}


class TimelineAIGenerationError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class TimelineOperationError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
def find_unknown_fields(payload: dict[str, Any], allowed_fields: set[str]) -> list[str]:
    """依白名單回傳請求資料中的未知欄位。"""
    return sorted(set(payload.keys()) - allowed_fields)


def get_user_timeline_role(user_id: int, timeline_id: int) -> int | None:
    """取得使用者在單一專案中的角色。"""
    return get_timeline_role(timeline_id, user_id)


def get_task_access(user_id: int, task: Task) -> int | None:
    """解析任務存取角色（專案任務或獨立任務）。"""
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


def timeline_list_item_to_dict(
    timeline: Timeline,
    role: int,
    total_tasks: int,
    completed_tasks: int,
) -> dict[str, Any]:
    """序列化專案列表卡片回應資料。"""
    return build_response_payload(TimelineListItemResponse, {
        'id': timeline.id,
        'name': timeline.name,
        'startDate': timeline.start_date.isoformat() + 'Z' if timeline.start_date else None,
        'endDate': timeline.end_date.isoformat() + 'Z' if timeline.end_date else None,
        'remark': timeline.remark,
        'role': role,
        'totalTasks': total_tasks,
        'completedTasks': completed_tasks,
    })


def timeline_task_item_to_dict(
    task: Task,
    assignee_name: str | None,
    assistant_list: list[str],
    can_manage_members: bool = False,
) -> dict[str, Any]:
    """序列化專案任務詳情回應資料。"""
    return build_response_payload(TimelineTaskItemResponse, {
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
        'depends_on_task_ids': task.depends_on_task_ids or [],
        'can_manage_members': bool(can_manage_members),
    })


def timeline_member_item_to_dict(timeline_member: TimelineUser, user: Any) -> dict[str, Any]:
    """序列化專案成員回應資料。"""
    return build_response_payload(TimelineMemberResponse, {
        'user_id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email,
        'role': timeline_member.role,
    })


def _build_existing_tasks_info(timeline_id):
    existing_tasks = get_active_tasks_by_timeline_id(timeline_id)
    task_name_map = {task.task_id: task.name for task in existing_tasks}

    existing_tasks_info = []
    for task in existing_tasks:
        estimated_days = 3
        if task.start_date and task.end_date:
            estimated_days = (task.end_date - task.start_date).days

        depends_on_task_ids = []
        for raw_dep_id in task.depends_on_task_ids or []:
            dep_id = _to_int(raw_dep_id)
            if dep_id is None or dep_id <= 0:
                continue
            if dep_id in depends_on_task_ids:
                continue
            depends_on_task_ids.append(dep_id)

        depends_on_task_refs = []
        for dep_id in depends_on_task_ids:
            dep_name = task_name_map.get(dep_id)
            if dep_name:
                depends_on_task_refs.append(dep_name)

        existing_tasks_info.append(
            {
                'task_id': task.task_id,
                'name': task.name,
                'priority': task.priority,
                'estimated_days': estimated_days,
                'task_remark': task.task_remark or '',
                'depends_on_task_ids': depends_on_task_ids,
                'depends_on_task_refs': depends_on_task_refs,
                'isExisting': True,
            }
        )

    return existing_tasks_info


def _normalize_dependency_ids(raw_values):
    if not isinstance(raw_values, list):
        return []

    normalized = []
    seen = set()
    for item in raw_values:
        task_id = _to_int(item)
        if task_id is None or task_id <= 0 or task_id in seen:
            continue
        seen.add(task_id)
        normalized.append(task_id)

    return normalized


def _normalize_dependency_refs(raw_values):
    if not isinstance(raw_values, list):
        return []

    normalized = []
    seen = set()
    for item in raw_values:
        if not isinstance(item, str):
            continue
        value = item.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)

    return normalized


def _normalize_generated_tasks(generated_tasks: Any, timeline_id: int) -> list[dict[str, Any]]:
    if not isinstance(generated_tasks, list):
        raise TimelineAIGenerationError('invalid_payload', 'AI 回傳格式錯誤')

    normalized_tasks = []
    for task in generated_tasks:
        if not isinstance(task, dict):
            raise TimelineAIGenerationError('invalid_payload', 'AI 回傳格式錯誤')

        depends_on_task_ids = _normalize_dependency_ids(task.get('depends_on_task_ids'))
        depends_on_task_refs = _normalize_dependency_refs(task.get('depends_on_task_refs'))

        # 若 AI 沒明確給依賴，預設以生成順序串成鏈，避免全為空依賴。
        if len(depends_on_task_ids) == 0 and len(depends_on_task_refs) == 0 and len(normalized_tasks) > 0:
            previous_task_name = str(normalized_tasks[-1].get('name') or '').strip()
            if previous_task_name:
                depends_on_task_refs = [previous_task_name]

        normalized = {
            'timeline_id': timeline_id,
            'status': 'pending',
            'completed': False,
            'isExisting': False,
            'name': task.get('name', '未命名任務'),
            'priority': task.get('priority', 2),
            'estimated_days': task.get('estimated_days', 3),
            'task_remark': task.get('task_remark', ''),
            'depends_on_task_ids': depends_on_task_ids,
            'depends_on_task_refs': depends_on_task_refs,
        }
        normalized_tasks.append(normalized)

    return normalized_tasks


def generate_timeline_tasks_with_ai(
    timeline_id: int,
    project_name: str,
    description: str = '',
    actor_user_id: int | None = None,
) -> dict[str, Any]:
    """以既有任務脈絡讓 AI 生成專案任務建議。

    例外:
        TimelineAIGenerationError: AI payload invalid or provider invocation failure.
    """
    timeline = get_active_timeline_or_404(timeline_id)
    if actor_user_id is not None:
        member = get_timeline_member(timeline_id, actor_user_id)
        if timeline.user_id != actor_user_id and member is None:
            raise TimelineOperationError('你沒有權限讀取此專案', 403)

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

    return build_response_payload(TimelineGenerateTasksResponse, {
        'message': f'現有 {len(existing_tasks_info)} 個任務，AI 生成 {len(generated_tasks)} 個新任務',
        'tasks': all_tasks,
        'existingCount': len(existing_tasks_info),
        'generatedCount': len(generated_tasks),
    }, exclude_none=True)


def _utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_active_timeline_or_404(timeline_id: int) -> Timeline:
    """依專案識別碼載入有效專案，找不到時拋錯。"""
    timeline = get_active_timeline_by_id(timeline_id)
    if not timeline:
        raise TimelineOperationError('找不到該專案', 404)
    return timeline


def list_timeline_items_for_user(user_id: int) -> list[dict[str, Any]]:
    """列出使用者可見的專案卡片，含任務計數。"""
    memberships = get_timeline_memberships_for_user_ordered_desc(user_id)
    timeline_ids = [timeline.id for timeline, _role in memberships]
    tasks = get_active_tasks_by_timeline_ids(timeline_ids)

    task_count_map = defaultdict(lambda: {'total': 0, 'completed': 0})
    for task in tasks:
        task_count_map[task.timeline_id]['total'] += 1
        if task.completed:
            task_count_map[task.timeline_id]['completed'] += 1

    result = []
    for timeline, role in memberships:
        total_tasks = task_count_map[timeline.id]['total']
        completed_tasks = task_count_map[timeline.id]['completed']
        result.append(timeline_list_item_to_dict(timeline, role, total_tasks, completed_tasks))
    return result


def create_timeline_for_user(user_id: int, data: dict[str, Any]) -> int:
    """建立專案並建立預設擁有者成員關係。

    例外:
        TimelineOperationError: 驗證失敗或資料寫入失敗。
    """
    try:
        create_input = TimelineCreateInput.model_validate(data)
    except ValidationError as err:
        first_error = err.errors()[0] if err.errors() else {}
        raise TimelineOperationError(str(first_error.get("msg") or "參數格式錯誤"), 400) from err

    new_timeline = build_timeline_entity(
        user_id=user_id,
        name=create_input.name.strip(),
        start_date=create_input.start_date,
        end_date=create_input.end_date,
        remark=create_input.remark,
    )

    with transaction(TimelineOperationError, '專案新增失敗，請稍後再試'):
        add_entity(new_timeline)
        flush_session()
        add_entity(build_timeline_member_entity(timeline_id=new_timeline.id, user_id=user_id, role=0))
    return new_timeline.id


def update_timeline_for_member(timeline_id: int, operator_user_id: int, data: dict[str, Any]) -> None:
    """Update editable timeline fields.

    例外:
        TimelineOperationError: payload 欄位無效或更新失敗。
    """
    timeline = get_active_timeline_or_404(timeline_id)
    member = get_timeline_member(timeline_id, operator_user_id)
    if timeline.user_id != operator_user_id and member is None:
        raise TimelineOperationError('你沒有權限操作此專案', 403)

    unknown_fields = find_unknown_fields(data, TIMELINE_UPDATE_ALLOWED_FIELDS)
    if unknown_fields:
        raise TimelineOperationError(f'不允許的欄位: {", ".join(unknown_fields)}', 400)
    try:
        update_input = TimelineUpdateInput.model_validate(data)
    except ValidationError as err:
        first_error = err.errors()[0] if err.errors() else {}
        raise TimelineOperationError(str(first_error.get("msg") or "參數格式錯誤"), 400) from err

    with transaction(TimelineOperationError, '專案更新失敗，請稍後再試'):
        if 'name' in data:
            timeline.name = update_input.name.strip()

        if 'start_date' in data:
            timeline.start_date = update_input.start_date

        if 'end_date' in data:
            timeline.end_date = update_input.end_date

        if 'remark' in data:
            timeline.remark = update_input.remark


def soft_delete_timeline_for_owner(timeline_id: int) -> None:
    """軟刪除專案與其關聯任務。"""
    timeline = get_active_timeline_or_404(timeline_id)

    with transaction(TimelineOperationError, '專案刪除失敗，請稍後再試'):
        deleted_at = _utcnow_naive()
        timeline.deleted_at = deleted_at
        soft_delete_tasks_by_timeline_id(timeline_id, deleted_at)


def list_timeline_tasks_detail(timeline_id: int, viewer_user_id: int | None = None) -> list[dict[str, Any]]:
    """列出專案的任務詳情清單。"""
    tasks = get_active_tasks_by_timeline_id_ordered_end_date(timeline_id)
    task_ids = [task.task_id for task in tasks]
    task_users = get_task_users_by_task_ids(task_ids)
    viewer_id = _to_int(viewer_user_id)

    viewer_is_timeline_owner = False
    if viewer_id is not None:
        timeline = get_active_timeline_by_id(timeline_id)
        viewer_is_timeline_owner = bool(timeline and timeline.user_id == viewer_id)

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
        viewer_is_task_owner = viewer_id is not None and task.user_id == viewer_id
        viewer_is_task_lead = False

        for task_user in task_user_map.get(task.task_id, []):
            user = users_map.get(task_user.user_id)
            if not user:
                continue
            if task_user.role == 0 and assignee_name is None:
                assignee_name = user.name
            elif task_user.role == 1:
                assistant_list.append(user.name)

            if viewer_id is not None and task_user.user_id == viewer_id and task_user.role == 0:
                viewer_is_task_lead = True

        can_manage_members = viewer_is_timeline_owner or viewer_is_task_owner or viewer_is_task_lead

        result.append(
            timeline_task_item_to_dict(
                task,
                assignee_name,
                assistant_list,
                can_manage_members=can_manage_members,
            )
        )

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


def _to_bool(value, default=False):
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value != 0

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {'1', 'true', 'yes', 'on'}:
            return True
        if normalized in {'0', 'false', 'no', 'off'}:
            return False

    return default


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


def _validate_weekly_report_input(start_date_raw, end_date_raw):
    try:
        payload = WeeklyReportInput(
            start_date_raw=start_date_raw,
            end_date_raw=end_date_raw,
        )
    except ValidationError as err:
        first_error = err.errors()[0] if err.errors() else {}
        message = str(first_error.get('msg') or '參數格式錯誤')
        raise TimelineOperationError(message, 400) from err
    return payload


def _validate_conflict_payload(payload):
    if not isinstance(payload, dict):
        raise TimelineOperationError('請提供正確的 JSON 物件', 400)

    try:
        return ConflictCheckInput.model_validate(payload)
    except ValidationError as err:
        first_error = err.errors()[0] if err.errors() else {}
        message = str(first_error.get('msg') or '參數格式錯誤')
        raise TimelineOperationError(message, 400) from err


def _validate_batch_task_payloads(task_payloads):
    try:
        payload = TimelineBatchCreateTasksInput(task_payloads=task_payloads)
    except ValidationError as err:
        first_error = err.errors()[0] if err.errors() else {}
        message = str(first_error.get('msg') or '參數格式錯誤')
        raise TimelineOperationError(message, 400) from err
    return payload.task_payloads


def _collect_selected_existing_task_ids(task_payloads, existing_task_id_set):
    selected_existing_task_ids = []
    for task_data in task_payloads:
        if not isinstance(task_data, dict):
            raise TimelineOperationError('tasks 格式錯誤，項目必須是物件', 400)

        task_id = _to_int(task_data.get('task_id'))
        if not task_data.get('isExisting') or task_id is None:
            continue
        if task_id not in existing_task_id_set:
            continue
        if task_id not in selected_existing_task_ids:
            selected_existing_task_ids.append(task_id)
    return selected_existing_task_ids


def _build_new_batch_tasks(timeline_id, user_id, timeline_start_date, task_payloads):
    created_task_names = []
    pending_dependency_records = []
    current_date = timeline_start_date

    for task_data in task_payloads:
        if task_data.get('isExisting'):
            continue

        estimated_days = _to_int(task_data.get('estimated_days'))
        if estimated_days is None or estimated_days <= 0:
            estimated_days = 3
        end_date = current_date + timedelta(days=estimated_days)

        new_task = build_timeline_task_entity(
            user_id=user_id,
            timeline_id=timeline_id,
            name=task_data.get('name', '未命名任務'),
            priority=task_data.get('priority', 2),
            status=task_data.get('status', 'pending'),
            task_remark=task_data.get('task_remark', ''),
            start_date=current_date,
            end_date=end_date,
            is_work=1,
        )
        add_entity(new_task)
        created_task_names.append(new_task.name)
        pending_dependency_records.append(
            {
                'task': new_task,
                'depends_on_task_ids': _normalize_dependency_ids(task_data.get('depends_on_task_ids')),
                'depends_on_task_refs': _normalize_dependency_refs(task_data.get('depends_on_task_refs')),
            }
        )
        current_date = end_date

    return created_task_names, pending_dependency_records


def _resolve_batch_task_dependencies(retained_existing_tasks, pending_dependency_records):
    valid_dependency_ids = {task.task_id for task in retained_existing_tasks}

    name_to_task_ids = defaultdict(list)
    for task in retained_existing_tasks:
        task_name = (task.name or '').strip()
        if task_name:
            name_to_task_ids[task_name].append(task.task_id)

    for record in pending_dependency_records:
        task = record['task']
        valid_dependency_ids.add(task.task_id)

        task_name = (task.name or '').strip()
        if task_name:
            name_to_task_ids[task_name].append(task.task_id)

    ignored_dependency_ref_count = 0
    ignored_dependency_id_count = 0
    for record in pending_dependency_records:
        task = record['task']
        dependency_ids = list(record['depends_on_task_ids'])

        for dependency_ref in record['depends_on_task_refs']:
            candidate_ids = name_to_task_ids.get(dependency_ref, [])
            resolved_id = next((cid for cid in reversed(candidate_ids) if cid != task.task_id), None)
            if resolved_id is None:
                ignored_dependency_ref_count += 1
                continue
            dependency_ids.append(resolved_id)

        normalized_dependency_ids = []
        seen_dependency_ids = set()
        for dependency_id in dependency_ids:
            if dependency_id in seen_dependency_ids:
                continue
            if dependency_id == task.task_id:
                ignored_dependency_id_count += 1
                continue
            if dependency_id not in valid_dependency_ids:
                ignored_dependency_id_count += 1
                continue
            seen_dependency_ids.add(dependency_id)
            normalized_dependency_ids.append(dependency_id)

        task.depends_on_task_ids = normalized_dependency_ids

    return ignored_dependency_ref_count, ignored_dependency_id_count


def _build_weekly_report_ai_cache_key(timeline_id, start_date, end_date, status_text):
    digest = hashlib.sha1(status_text.encode('utf-8')).hexdigest()[:12]
    return f"{timeline_id}:{start_date.isoformat()}:{end_date.isoformat()}:{digest}"


def _get_cached_weekly_report_ai_summary(cache_key):
    cached = _WEEKLY_REPORT_AI_SUMMARY_CACHE.get(cache_key)
    if not cached:
        return None

    expires_at, summary = cached
    if time.time() >= expires_at:
        _WEEKLY_REPORT_AI_SUMMARY_CACHE.pop(cache_key, None)
        return None

    return summary


def _set_cached_weekly_report_ai_summary(cache_key, summary):
    if not summary:
        return

    _WEEKLY_REPORT_AI_SUMMARY_CACHE[cache_key] = (
        time.time() + WEEKLY_REPORT_AI_CACHE_TTL_SEC,
        summary,
    )


def _invoke_weekly_report_ai_summary(provider, status_text):
    llm = get_default_llm(provider=provider)
    return generate_weekly_report_summary(llm=llm, status_text=status_text)


def _safe_generate_weekly_report_ai_summary(timeline_id, start_date, end_date, status_text, fallback):
    cache_key = _build_weekly_report_ai_cache_key(timeline_id, start_date, end_date, status_text)
    cached = _get_cached_weekly_report_ai_summary(cache_key)
    if cached:
        return cached, 'cache'

    provider = os.getenv('LLM_PROVIDER', 'google-generativeai')
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='weekly-report-ai')
    future = executor.submit(_invoke_weekly_report_ai_summary, provider, status_text)

    try:
        generated = str(future.result(timeout=WEEKLY_REPORT_AI_TIMEOUT_SEC)).strip()
        if generated:
            _set_cached_weekly_report_ai_summary(cache_key, generated)
            return generated, 'llm'
        return fallback, 'fallback-empty'
    except FutureTimeoutError:
        future.cancel()
        return fallback, 'fallback-timeout'
    except Exception:
        return fallback, 'fallback-error'
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


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


def _build_conflict_risk_context_text(timeline, conflicts):
    if not conflicts:
        return '無'

    timeline_conflict_task_ids = []
    seen = set()
    for item in conflicts:
        if item.get('is_cross_project'):
            continue
        task_id = _to_int(item.get('task_id'))
        if task_id is None or task_id in seen:
            continue
        seen.add(task_id)
        timeline_conflict_task_ids.append(task_id)

    if not timeline_conflict_task_ids:
        return '目前衝突以跨專案任務為主，暫無可對應的專案內風險分析項目。'

    try:
        analysis = build_critical_path_analysis_payload(
            timeline=timeline,
            tasks=get_active_tasks_by_timeline_id(timeline.id),
        )
    except Exception:
        return '風險分析暫時不可用，請先依衝突明細調整排程。'

    critical_path_task_ids = {
        _to_int(item.get('task_id'))
        for item in analysis.get('critical_path', [])
        if _to_int(item.get('task_id')) is not None
    }

    risk_item_map = {}
    for risk_item in analysis.get('risk_items', []):
        task_id = _to_int(risk_item.get('task_id'))
        if task_id is None:
            continue
        risk_item_map[task_id] = risk_item

    lines = []
    for task_id in timeline_conflict_task_ids[:5]:
        matched_conflict = next(
            (
                item
                for item in conflicts
                if (not item.get('is_cross_project')) and _to_int(item.get('task_id')) == task_id
            ),
            None,
        )

        display_name = matched_conflict.get('name') if matched_conflict else f'任務#{task_id}'

        risk_item = risk_item_map.get(task_id) or {}
        severity = str(risk_item.get('severity') or 'low').upper()
        impact_days = _to_int(risk_item.get('impact_days')) or 0
        is_critical = '是' if task_id in critical_path_task_ids else '否'

        lines.append(
            f"- {display_name}（task_id={task_id}）：critical_path={is_critical}；severity={severity}；impact_days={impact_days}"
        )

    summary = analysis.get('summary') or {}
    risk_lines = '\n'.join(lines)
    return (
        f"專案風險摘要：高風險 {summary.get('high_risk_count', 0)} 項，"
        f"關鍵路徑 {summary.get('critical_path_task_count', 0)} 項，"
        f"預估總工期 {summary.get('projected_duration_days', 0)} 天。\n"
        f"衝突任務風險：\n{risk_lines}"
    )


def build_timeline_risk_analysis(timeline_id: int) -> dict[str, Any]:
    """建立專案關鍵路徑與風險分析結果。"""
    timeline = get_active_timeline_or_404(timeline_id)
    tasks = get_active_tasks_by_timeline_id(timeline_id)

    payload = build_critical_path_analysis_payload(
        timeline=timeline,
        tasks=tasks,
    )
    payload['message'] = '風險分析完成'
    return payload


def trigger_timeline_risk_notifications(timeline_id: int) -> dict[str, Any]:
    """從專案分析生成並儲存風險通知。"""
    timeline = get_active_timeline_or_404(timeline_id)
    analysis = build_timeline_risk_analysis(timeline_id)

    risk_items = analysis.get('risk_items', [])
    high_risk_items = [item for item in risk_items if item.get('severity') == 'high']
    warning_count = len(analysis.get('warnings', []))

    if len(risk_items) == 0:
        return build_response_payload(TimelineRiskNotificationResponse, {
            'message': '目前無風險項目，未發送通知',
            'timeline_id': timeline_id,
            'risk_item_count': 0,
            'high_risk_count': 0,
            'warning_count': warning_count,
            'notified_user_count': 0,
        })

    members = get_timeline_members(timeline_id)
    notified_user_ids = sorted({member.user_id for member in members})

    if len(notified_user_ids) == 0:
        return build_response_payload(TimelineRiskNotificationResponse, {
            'message': '專案目前無成員，未發送通知',
            'timeline_id': timeline_id,
            'risk_item_count': len(risk_items),
            'high_risk_count': len(high_risk_items),
            'warning_count': warning_count,
            'notified_user_count': 0,
        })

    preview_names = [item.get('name') for item in high_risk_items[:3] if item.get('name')]
    if len(preview_names) == 0:
        preview_names = [item.get('name') for item in risk_items[:3] if item.get('name')]
    preview_text = '、'.join(preview_names) if preview_names else '請查看風險分析面板'

    if len(high_risk_items) > 0:
        title = f'「{timeline.name}」有 {len(high_risk_items)} 項高風險任務'
    else:
        title = f'「{timeline.name}」有 {len(risk_items)} 項排程風險'

    content = (
        f'重點任務：{preview_text}。'
        f'請至專案風險分析確認 impact 與建議動作。'
    )

    with transaction(TimelineOperationError, '風險通知發送失敗，請稍後再試'):
        for user_id in notified_user_ids:
            add_entity(
                Notification(
                    user_id=user_id,
                    type='risk_alert',
                    title=title,
                    content=content,
                    link='/timelines',
                )
            )

    return build_response_payload(TimelineRiskNotificationResponse, {
        'message': '風險通知已發送',
        'timeline_id': timeline_id,
        'risk_item_count': len(risk_items),
        'high_risk_count': len(high_risk_items),
        'warning_count': warning_count,
        'notified_user_count': len(notified_user_ids),
    })


def build_weekly_report_for_timeline(
    timeline_id: int,
    start_date_raw: str | None = None,
    end_date_raw: str | None = None,
) -> dict[str, Any]:
    """建立每週專案報告，並可選擇附上 AI 摘要。"""
    timeline = get_active_timeline_or_404(timeline_id)
    input_payload = _validate_weekly_report_input(start_date_raw, end_date_raw)
    start_date, end_date = _normalize_report_period(
        input_payload.start_date_raw,
        input_payload.end_date_raw,
    )

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
    ai_summary, ai_summary_source = _safe_generate_weekly_report_ai_summary(
        timeline_id=timeline.id,
        start_date=start_date,
        end_date=end_date,
        status_text=status_text,
        fallback=ai_summary,
    )

    return build_response_payload(WeeklyReportResponse, {
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
        'ai_summary_source': ai_summary_source,
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
            'ai_summary_source': ai_summary_source,
        },
    })


def check_timeline_task_conflicts(
    timeline_id: int,
    payload: dict[str, Any],
    actor_user_id: int,
) -> dict[str, Any]:
    """Check timeline task conflicts before batch apply.

    例外:
        TimelineOperationError: payload 無效、權限不足或衝突解決失敗。
    """
    input_payload = _validate_conflict_payload(payload)
    timeline = get_active_timeline_or_404(timeline_id)

    end_date = input_payload.end_date
    start_date = input_payload.start_date

    window_start_dt = datetime.combine(start_date, datetime.min.time())
    window_end_dt = datetime.combine(end_date, datetime.max.time())

    assignee_user_id = input_payload.assignee_user_id or actor_user_id
    excluded_task_id = input_payload.task_id
    task_name = input_payload.name
    task_priority = input_payload.priority
    priority_label = _priority_label(task_priority)

    assignee_member = get_timeline_member(timeline_id, assignee_user_id)
    if assignee_member is None:
        raise TimelineOperationError('assignee_user_id 必須是專案成員', 400)

    assignee_user = get_user_by_id(assignee_user_id)
    assignee_name = assignee_user.name if assignee_user else None
    should_mask_task_names = assignee_user_id != actor_user_id

    assignee_task_id_set = set(list_task_ids_by_assignee_user_id(assignee_user_id))

    all_tasks = get_active_incomplete_tasks_by_timeline_id(timeline_id)
    candidates = [
        task for task in all_tasks if excluded_task_id is None or task.task_id != excluded_task_id
    ]

    candidate_task_id_set = {task.task_id for task in candidates}
    assignee_task_ids = assignee_task_id_set.intersection(candidate_task_id_set)

    users_map = {
        user.id: user.name
        for user in get_users_by_ids({task.user_id for task in candidates})
    }

    cross_project_tasks = list_cross_project_active_tasks_for_assignee(
        assignee_user_id=assignee_user_id,
        current_timeline_id=timeline_id,
        assignee_task_id_set=assignee_task_id_set,
        excluded_task_id=excluded_task_id,
        window_start=window_start_dt,
        window_end=window_end_dt,
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

    cross_project_owner_ids = {task.user_id for task in cross_project_tasks}
    if cross_project_owner_ids:
        users_map.update(
            {
                user.id: user.name
                for user in get_users_by_ids(cross_project_owner_ids)
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
        window_start=window_start_dt,
        window_end=window_end_dt,
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
    env_ai_suggestion_enabled = str(
        os.getenv('CONFLICT_CHECK_ENABLE_AI_SUGGESTION', 'false')
    ).strip().lower() in {'1', 'true', 'yes', 'on'}
    include_ai_suggestion = _to_bool(
        input_payload.include_ai_suggestion,
        default=env_ai_suggestion_enabled,
    )

    # Phase 7.1：使用 chains 層的 LangChain 生成 AI 衝突建議
    ai_suggestion_text = ""
    if has_conflict and suggestion and include_ai_suggestion:
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
        risk_context_text = _build_conflict_risk_context_text(timeline, conflicts)
        try:
            provider = os.getenv('LLM_PROVIDER', 'google-generativeai')
            llm = get_default_llm(provider=provider)
            ai_suggestion_text = generate_conflict_suggestion(
                llm=llm,
                conflict_text=conflict_summary,
                suggestion_date_range=suggestion_range,
                risk_context_text=risk_context_text,
            )
        except Exception:
            ai_suggestion_text = ""

    message = '未偵測到排程衝突'
    if has_conflict:
        message = f'偵測到 {len(conflicts)} 個日期衝突'
        if workload_overload_count:
            message += f'，另有 {workload_overload_count} 天工作量過載'

    return build_response_payload(TimelineConflictCheckResponse, {
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
        'include_ai_suggestion': include_ai_suggestion,
    })


def update_timeline_remark_for_member(timeline_id: int, remark: str) -> None:
    """更新專案備註文字。"""
    timeline = get_active_timeline_or_404(timeline_id)

    if not isinstance(remark, str):
        raise TimelineOperationError('備註必須是字串', 400)

    with transaction(TimelineOperationError, '備註更新失敗，請稍後再試'):
        timeline.remark = remark


def search_timeline_user_by_email(timeline_id: int, requester_user_id: int, email: str) -> dict[str, Any]:
    """以電子郵件搜尋可加入的專案成員候選人，並套用成員保護規則。"""
    if timeline_id in (None, ''):
        raise TimelineOperationError('請提供 timeline_id', 400)

    if not email:
        raise TimelineOperationError('請提供 Email', 400)

    timeline = get_active_timeline_or_404(timeline_id)
    member = get_timeline_member(timeline_id, requester_user_id)
    if timeline.user_id != requester_user_id and member is None:
        raise TimelineOperationError('您不是該專案成員', 403)

    user = get_user_by_email(email)
    if not user:
        raise TimelineOperationError('找不到該使用者', 404)

    return user


def list_timeline_members_payload(timeline_id: int) -> list[dict[str, Any]]:
    """列出專案成員清單資料。"""
    members = get_timeline_members(timeline_id)
    users_map = {user.id: user for user in get_users_by_ids([member.user_id for member in members])}

    result = []
    for member in members:
        user = users_map.get(member.user_id)
        if user:
            result.append(timeline_member_item_to_dict(member, user))
    return result


def add_timeline_member_for_owner(
    timeline_id: int,
    invited_user_id: int,
    role: int,
    actor_user_id: int,
) -> dict[str, Any]:
    """新增專案成員並發送邀請通知。"""
    if not invited_user_id:
        raise TimelineOperationError('請提供使用者 ID', 400)

    with transaction(TimelineOperationError, '成員新增失敗，請稍後再試'):
        member = TimelineUser(timeline_id=timeline_id, user_id=invited_user_id, role=role)
        add_entity(member)

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
        add_entity(notif)

    invited_user = get_user_by_id(invited_user_id)
    if invited_user is None:
        raise TimelineOperationError('找不到新增後的成員資料', 500)
    return timeline_member_item_to_dict(member, invited_user)


def remove_timeline_member_for_owner(timeline_id: int, member_user_id: int, operator_user_id: int) -> None:
    """由擁有者移除專案成員。"""
    if member_user_id == operator_user_id:
        raise TimelineOperationError('不能將自己移出專案', 400)

    member = get_timeline_member(timeline_id, member_user_id)
    if not member or member.role == 0:
        raise TimelineOperationError('找不到該成員，或無法移除負責人', 404)

    with transaction(TimelineOperationError, '成員移除失敗，請稍後再試'):
        delete_entity(member)


def batch_create_tasks_for_timeline(
    timeline_id: int,
    user_id: int,
    task_payloads: list[dict[str, Any]],
) -> dict[str, Any]:
    """Batch create timeline tasks from normalized payloads.

    例外:
        TimelineOperationError: 驗證失敗、相依檢查失敗或資料寫入失敗。
    """
    timeline = get_active_timeline_or_404(timeline_id)
    member = get_timeline_member(timeline_id, user_id)
    if timeline.user_id != user_id and member is None:
        raise TimelineOperationError('你沒有權限操作此專案', 403)
    task_payloads = _validate_batch_task_payloads(task_payloads)

    with transaction(TimelineOperationError, '批次建立任務失敗，請稍後再試'):
        existing_tasks = get_active_tasks_by_timeline_id(timeline_id)
        all_existing_task_ids = [task.task_id for task in existing_tasks]
        existing_task_id_set = set(all_existing_task_ids)

        selected_existing_task_ids = _collect_selected_existing_task_ids(
            task_payloads=task_payloads,
            existing_task_id_set=existing_task_id_set,
        )

        tasks_to_delete = set(all_existing_task_ids) - set(selected_existing_task_ids)
        if tasks_to_delete:
            soft_delete_tasks_by_ids(list(tasks_to_delete), _utcnow_naive())

        retained_existing_tasks = [task for task in existing_tasks if task.task_id in selected_existing_task_ids]
        start_date = timeline.start_date or datetime.now()
        created_task_names, pending_dependency_records = _build_new_batch_tasks(
            timeline_id=timeline_id,
            user_id=user_id,
            timeline_start_date=start_date,
            task_payloads=task_payloads,
        )

        flush_session()

        ignored_dependency_ref_count, ignored_dependency_id_count = _resolve_batch_task_dependencies(
            retained_existing_tasks=retained_existing_tasks,
            pending_dependency_records=pending_dependency_records,
        )

    message = (
        f'保留 {len(selected_existing_task_ids)} 個舊任務，'
        f'刪除 {len(tasks_to_delete)} 個舊任務，新增 {len(created_task_names)} 個任務'
    )
    if ignored_dependency_ref_count > 0:
        message += f'，忽略 {ignored_dependency_ref_count} 個無法解析的前置依賴'
    if ignored_dependency_id_count > 0:
        message += f'，忽略 {ignored_dependency_id_count} 個無效的前置依賴 ID'

    return build_response_payload(TimelineBatchCreateTasksResponse, {
        'message': message,
        'kept': len(selected_existing_task_ids),
        'deleted': len(tasks_to_delete),
        'created': len(created_task_names),
        'ignored_dependency_refs': ignored_dependency_ref_count,
        'ignored_dependency_ids': ignored_dependency_id_count,
    })


def list_upcoming_timelines_for_user(user_id: int) -> list[dict[str, Any]]:
    """列出即將開始的專案供提醒流程使用。"""
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
                build_response_payload(UpcomingTimelineResponse, {
                    'id': timeline.id,
                    'name': timeline.name,
                    'end_date': end.isoformat(),
                    'role': role,
                    'is_overdue': end < today,
                    'type': 'timeline',
                })
            )

    return result


def build_timeline_member_stats_payload(timeline_id: int) -> dict[str, Any]:
    """建立專案內每位成員的統計資料。"""
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

    return build_response_payload(TimelineMemberStatsResponse, {
        'members': sorted(members_payload, key=lambda item: -item['total_tasks']),
        'status_distribution': status_dist,
        'total_tasks': len(tasks),
    })


