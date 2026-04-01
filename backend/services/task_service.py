from functools import wraps
import json
import os
import re

from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from models import db
from models.notification import Notification
from models.task import Task
from models.task_user import TaskUser
from models.timeline_user import TimelineUser
from models.user import User

TASK_CREATE_ALLOWED_FIELDS = {
    'name',
    'timeline_id',
    'priority',
    'status',
    'tags',
    'estimated_hours',
    'start_date',
    'end_date',
    'task_remark',
    'isWork',
}

TASK_UPDATE_ALLOWED_FIELDS = {
    'name',
    'timeline_id',
    'priority',
    'status',
    'tags',
    'estimated_hours',
    'actual_hours',
    'start_date',
    'end_date',
    'task_remark',
    'isWork',
}

TASK_STATUS_VALUES = {'pending', 'in_progress', 'review', 'completed', 'cancelled'}


def find_unknown_fields(payload, allowed_fields):
    return sorted(set(payload.keys()) - allowed_fields)


def create_notification(user_id, ntype, title, content=None, link=None):
    """建立通知的工具函式，失敗時靜默不影響主流程。"""
    try:
        notif = Notification(
            user_id=user_id,
            type=ntype,
            title=title,
            content=content,
            link=link,
        )
        db.session.add(notif)
    except Exception:
        pass


def get_user_task_role(user_id, task_id):
    """查詢使用者在某任務的角色。"""
    member = TaskUser.query.filter_by(task_id=task_id, user_id=user_id).first()
    if member:
        return member.role

    task = Task.query.filter_by(task_id=task_id).first()
    if task and task.timeline_id:
        tl_member = TimelineUser.query.filter_by(
            timeline_id=task.timeline_id,
            user_id=user_id,
        ).first()
        if tl_member is not None:
            return tl_member.role

    return None


def can_manage_task_members(operator_user_id, task):
    """檢查是否可管理任務成員（任務主責/建立者/專案主責）。"""
    task_role = get_user_task_role(operator_user_id, task.task_id)
    is_task_owner = (task_role == 0) or (task.user_id == operator_user_id)

    is_timeline_owner = False
    if task.timeline_id:
        tl_role = TimelineUser.query.filter_by(
            timeline_id=task.timeline_id,
            user_id=operator_user_id,
        ).first()
        is_timeline_owner = tl_role is not None and tl_role.role == 0

    return is_task_owner or is_timeline_owner


def require_task_role(required_role='member'):
    """Decorator：檢查當前使用者在任務中的角色。"""

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_id = int(get_jwt_identity())
            task_id = kwargs.get('task_id')
            role = get_user_task_role(user_id, task_id)
            if role is None:
                return jsonify({'error': '你不是此任務成員'}), 403
            if required_role == 'owner' and role != 0:
                return jsonify({'error': '只有負責人可執行此操作'}), 403
            return f(*args, **kwargs)

        return wrapper

    return decorator


def task_member_to_dict(task_member, user, include_contact=False):
    payload = {
        'user_id': user.id,
        'name': user.name,
        'role': task_member.role,
    }

    if include_contact:
        payload['email'] = user.email
        payload['avatar'] = user.avatar
        payload['assigned_at'] = task_member.assigned_at.isoformat() + 'Z' if task_member.assigned_at else None

    return payload


def build_task_member_list(task_id, viewer_user_id=None, include_contact=False):
    members = TaskUser.query.filter_by(task_id=task_id).all()
    result = []
    viewer_role = None

    for member in members:
        if viewer_user_id is not None and member.user_id == viewer_user_id:
            viewer_role = member.role

        user = db.session.get(User, member.user_id)
        if user:
            result.append(task_member_to_dict(member, user, include_contact=include_contact))

    return result, viewer_role


def task_list_item_to_dict(task, member_list, subtask_list, is_owner):
    return {
        'task_id': task.task_id,
        'name': task.name,
        'completed': task.completed,
        'timeline_id': task.timeline_id,
        'priority': task.priority,
        'status': task.status,
        'tags': task.tags,
        'estimated_hours': task.estimated_hours,
        'actual_hours': task.actual_hours,
        'members': member_list,
        'subtasks': subtask_list,
        'created_at': task.created_at.isoformat() + 'Z' if task.created_at else None,
        'start_date': task.start_date.isoformat() + 'Z' if task.start_date else None,
        'end_date': task.end_date.isoformat() + 'Z' if task.end_date else None,
        'updated_at': task.updated_at.isoformat() + 'Z' if task.updated_at else None,
        'task_remark': task.task_remark,
        'isWork': task.isWork,
        'is_owner': is_owner,
    }


def task_comment_to_dict(comment, user):
    return {
        'comment_id': comment.comment_id,
        'user_id': comment.user_id,
        'user_name': user.name if user else '未知使用者',
        'user_avatar': user.avatar if user else None,
        'task_message': comment.task_message,
        'created_at': comment.created_at.isoformat() + 'Z' if comment.created_at else None,
    }


def _to_clean_list(value, max_items=3):
    if isinstance(value, str):
        candidates = [value]
    elif isinstance(value, list):
        candidates = value
    else:
        candidates = []

    normalized = []
    for item in candidates:
        if not isinstance(item, str):
            continue
        cleaned = item.strip().strip('-').strip()
        if cleaned:
            normalized.append(cleaned)

    return normalized[:max_items]


def _normalize_summary_payload(payload, raw_text=None):
    if not isinstance(payload, dict):
        payload = {}

    normalized = {
        'decisions': _to_clean_list(payload.get('decisions')),
        'risks': _to_clean_list(payload.get('risks')),
        'next_actions': _to_clean_list(payload.get('next_actions')),
    }

    if isinstance(raw_text, str) and raw_text.strip():
        normalized['raw'] = raw_text.strip()

    return normalized


def _strip_markdown_fence(text):
    stripped = text.strip()
    if stripped.startswith('```'):
        stripped = re.sub(r'^```(?:json)?\s*', '', stripped, flags=re.IGNORECASE)
        stripped = re.sub(r'\s*```$', '', stripped)
    return stripped.strip()


def _extract_first_json_object(text):
    if not isinstance(text, str):
        return None

    start = text.find('{')
    if start < 0:
        return None

    depth = 0
    in_string = False
    escaped = False

    for i in range(start, len(text)):
        ch = text[i]

        if in_string:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]

    return None


def _parse_fallback_summary(raw_text):
    decisions = []
    risks = []
    next_actions = []

    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        decision_match = re.match(r'^(?:決議|決策|decisions?)\s*[:：]\s*(.+)$', stripped, flags=re.IGNORECASE)
        if decision_match:
            decisions.append(decision_match.group(1).strip())
            continue

        risk_match = re.match(r'^(?:風險|risks?)\s*[:：]\s*(.+)$', stripped, flags=re.IGNORECASE)
        if risk_match:
            risks.append(risk_match.group(1).strip())
            continue

        action_match = re.match(r'^(?:下一步|後續行動|next[_\s-]?actions?)\s*[:：]\s*(.+)$', stripped, flags=re.IGNORECASE)
        if action_match:
            next_actions.append(action_match.group(1).strip())

    return _normalize_summary_payload(
        {
            'decisions': decisions,
            'risks': risks,
            'next_actions': next_actions,
        },
        raw_text=raw_text,
    )


def build_task_comment_summary_context(task, comment_items, max_chars=12000):
    entries = []
    for item in comment_items:
        author = (item.get('user_name') or '未知使用者').strip()
        message = (item.get('task_message') or '').strip()
        created_at = (item.get('created_at') or '').replace('T', ' ').replace('Z', '')[:16]
        if not message:
            continue
        if created_at:
            entries.append(f"- [{created_at}] {author}: {message}")
        else:
            entries.append(f"- {author}: {message}")

    kept_entries_rev = []
    current_chars = 0
    for entry in reversed(entries):
        entry_len = len(entry) + 1
        if kept_entries_rev and current_chars + entry_len > max_chars:
            break

        if not kept_entries_rev and entry_len > max_chars:
            kept_entries_rev.append(entry[:max_chars])
            current_chars = max_chars
            break

        kept_entries_rev.append(entry)
        current_chars += entry_len

    kept_entries = list(reversed(kept_entries_rev))
    truncated = len(kept_entries) < len(entries)

    header_lines = [
        f"任務名稱: {task.name}",
        f"任務狀態: {task.status or 'pending'}",
        f"任務優先級: {task.priority if task.priority is not None else 2}",
        "",
        "留言紀錄（按時間排序）:",
    ]

    context = '\n'.join(header_lines + kept_entries)
    return context, {
        'total_comments': len(entries),
        'used_comments': len(kept_entries),
        'truncated': truncated,
        'context_chars': len(context),
    }


class _LMStudioRequestError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def _lmstudio_request_json(base_url, endpoint, payload=None, timeout=60):
    """使用 requests 庫調用 LM Studio API"""
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    method = 'GET' if payload is None else 'POST'
    
    print(f"📡 [LM Studio] {method} {url} | timeout={timeout}s", flush=True)

    try:
        if method == 'GET':
            print(f"📡 [LM Studio] 發送 GET 請求...", flush=True)
            response = requests.get(url, timeout=timeout)
        else:
            print(f"📡 [LM Studio] 發送 POST 請求...", flush=True)
            response = requests.post(url, json=payload, timeout=timeout)
        
        print(f"📡 [LM Studio] 收到回應 | status={response.status_code}", flush=True)
        response.raise_for_status()
        
        result = response.json()
        print(f"📡 [LM Studio] JSON 解析成功", flush=True)
        return result
        
    except requests.exceptions.Timeout:
        print(f"❌ [LM Studio] 逾時: {timeout}s", flush=True)
        raise _LMStudioRequestError('timeout', f'LM Studio 連線逾時 ({timeout}s)')
    except requests.exceptions.ConnectionError as e:
        print(f"❌ [LM Studio] 連線失敗: {str(e)}", flush=True)
        raise _LMStudioRequestError('unavailable', 'LM Studio 連線失敗')
    except requests.exceptions.HTTPError as e:
        print(f"❌ [LM Studio] HTTP {e.response.status_code}", flush=True)
        try:
            err_data = e.response.json()
            err = err_data.get('error', {})
            if isinstance(err, dict):
                code = err.get('code') or f'http_{e.response.status_code}'
                message = err.get('message') or str(e)
            else:
                code = f'http_{e.response.status_code}'
                message = str(err)
        except:
            code = f'http_{e.response.status_code}'
            message = e.response.text or str(e)
        
        print(f"❌ [LM Studio] error_code={code} | message={message[:100]}", flush=True)
        raise _LMStudioRequestError(code, message)
    except requests.exceptions.JSONDecodeError as e:
        print(f"❌ [LM Studio] JSON 解析失敗: {str(e)}", flush=True)
        raise _LMStudioRequestError('invalid_json', 'LM Studio 回應 JSON 解析失敗')
    except Exception as e:
        print(f"❌ [LM Studio] 未預期的錯誤: {type(e).__name__} - {str(e)}", flush=True)
        raise _LMStudioRequestError('error', str(e))


def _pick_chat_model(models):
    model_ids = []
    for item in models:
        if isinstance(item, dict):
            model_id = item.get('id')
            if isinstance(model_id, str) and model_id.strip():
                model_ids.append(model_id.strip())

    if not model_ids:
        return None

    for model_id in model_ids:
        lowered = model_id.lower()
        if 'embedding' in lowered or 'embed-' in lowered or 'nomic-embed' in lowered:
            continue
        return model_id

    return model_ids[0]


def generate_task_comment_summary(task, comment_items):
    """使用 Gemini AI 生成任務留言摘要（決議/風險/下一步）"""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        import google.generativeai as genai

    print(f"🤖 [AI Summary] 開始生成摘要 | task_id={task.task_id} | comments={len(comment_items)}", flush=True)
    context, meta = build_task_comment_summary_context(task, comment_items)

    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print(f"❌ [AI Summary] Google API Key 未配置", flush=True)
        raise RuntimeError('AI 摘要服務配置不完整，請稍後再試')

    genai.configure(api_key=api_key)
    print(f"🤖 [AI Summary] 使用 Gemini 2.5 Flash Lite", flush=True)

    system_prompt = (
        '你是專案任務摘要助手。\n'
        '請依據提供的任務留言，輸出嚴格 JSON 格式，內容必須只有以下欄位：\n'
        '{"decisions": string[], "risks": string[], "next_actions": string[]}\n'
        '規則：\n'
        '1) 每個陣列最多 3 條\n'
        '2) 每條一句話，重點清楚\n'
        '3) 若沒有內容請回傳空陣列\n'
        '4) 不要輸出任何 JSON 以外文字'
    )

    user_message = f"{system_prompt}\n\n留言內容：\n{context}"

    try:
        print(f"🤖 [AI Summary] 發送請求到 Gemini API...", flush=True)
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        response = model.generate_content(
            user_message,
            generation_config={
                'response_mime_type': 'application/json',
                'temperature': 0.2,
            }
        )
        print(f"🤖 [AI Summary] 收到回應", flush=True)

        raw_text = response.text
        print(f"📡 [Gemini] 回應文本長度={len(raw_text)}", flush=True)

    except Exception as e:
        print(f"❌ [AI Summary] Gemini 錯誤: {type(e).__name__} - {str(e)}", flush=True)
        raise RuntimeError('AI 摘要服務暫時不可用，請稍後再試')

    cleaned = _strip_markdown_fence(raw_text) if isinstance(raw_text, str) else ''
    if not cleaned:
        print(f"❌ [AI Summary] 清理後無內容", flush=True)
        raise RuntimeError('AI 摘要服務暫時不可用，請稍後再試')

    try:
        parsed_json = json.loads(cleaned)
        print(f"📡 [Gemini] JSON 解析成功", flush=True)
        summary = _normalize_summary_payload(parsed_json, raw_text=cleaned)
    except json.JSONDecodeError:
        print(f"❌ [Gemini] JSON 解析失敗，嘗試提取...", flush=True)
        extracted_json = _extract_first_json_object(cleaned)
        if extracted_json:
            try:
                parsed_json = json.loads(extracted_json)
                summary = _normalize_summary_payload(parsed_json, raw_text=cleaned)
            except json.JSONDecodeError:
                summary = _parse_fallback_summary(cleaned)
        else:
            summary = _parse_fallback_summary(cleaned)

    meta['model'] = 'gemini-2.5-flash-lite'
    print(f"✅ [AI Summary] 完成 | decisions={len(summary.get('decisions', []))} | risks={len(summary.get('risks', []))} | next_actions={len(summary.get('next_actions', []))}", flush=True)
    return summary, meta
