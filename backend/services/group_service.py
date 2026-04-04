from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import os
import random
import threading
import uuid

from models import db
from models.group import Group
from models.group import GroupMember
from models.group_ai_snapshot import GroupAISnapshot
from models.message import Message
from models.user import User
from repositories.group_repository import (
    get_group_by_invite_code,
    get_group_member,
    list_group_members_query,
    list_group_messages_query,
    list_groups_for_user_query,
)
from services.ai_provider import get_ai_provider


class GroupOperationError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


_snapshot_jobs = {}
_snapshot_jobs_lock = threading.Lock()
_snapshot_executor = ThreadPoolExecutor(max_workers=2)


def _utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _to_iso_z(value):
    if not value:
        return None
    return value.isoformat() + 'Z'


def _get_int_env(name, default_value):
    raw = os.getenv(name)
    if raw is None or raw == '':
        return default_value
    try:
        return int(raw)
    except ValueError:
        return default_value


def get_snapshot_chunk_size():
    return max(1, _get_int_env('SNAPSHOT_CHUNK_SIZE', 50))


def get_snapshot_async_threshold():
    return max(1, _get_int_env('SNAPSHOT_ASYNC_THRESHOLD', 500))


def get_snapshot_window_days_default():
    return max(1, _get_int_env('SNAPSHOT_WINDOW_DAYS', 30))


def generate_unique_invite_code():
    while True:
        invite_code = f"{random.randint(0, 999999):06d}"
        existing = get_group_by_invite_code(invite_code)
        if not existing:
            return invite_code


def group_to_dict(group):
    return {
        'group_id': group.group_id,
        'group_name': group.group_name,
        'group_type': group.group_type,
        'invite_code': group.group_inviteCode,
        'created_at': group.created_at.isoformat() + 'Z' if group.created_at else None,
    }


def group_member_to_dict(member):
    return {
        'user_id': member.id,
        'name': member.name,
        'email': member.email,
    }


def group_message_to_dict(message):
    return {
        'message_id': message.message_id,
        'content': message.content,
        'sender_name': message.sender_name,
        'created_at': message.created_at.isoformat() + 'Z' if message.created_at else None,
    }


def is_group_member(group_id, user_id):
    return get_group_member(group_id, user_id) is not None


def group_room_name(group_id):
    return f'group_{group_id}'


def list_groups_for_user(user_id):
    groups = list_groups_for_user_query(user_id)
    return [group_to_dict(group) for group in groups]


def create_group_for_user(user_id, group_name):
    normalized_name = group_name.strip() if isinstance(group_name, str) else ''
    if not normalized_name:
        raise GroupOperationError('請輸入群組名稱', 400)

    invite_code = generate_unique_invite_code()
    new_group = Group(
        group_name=normalized_name,
        group_type='task',
        group_inviteCode=invite_code,
        created_by=user_id,
    )

    try:
        db.session.add(new_group)
        db.session.flush()
        db.session.add(GroupMember(group_id=new_group.group_id, user_id=user_id))
        db.session.commit()
        return {
            'group_id': new_group.group_id,
            'invite_code': invite_code,
        }
    except Exception as exc:
        db.session.rollback()
        raise GroupOperationError('建立群組失敗，請稍後再試', 500) from exc


def join_group_by_invite_code(user_id, invite_code):
    normalized_code = invite_code.strip() if isinstance(invite_code, str) else ''
    if not normalized_code:
        raise GroupOperationError('請輸入邀請碼', 400)

    group = get_group_by_invite_code(normalized_code)
    if not group:
        raise GroupOperationError('邀請碼無效', 404)

    existing = get_group_member(group.group_id, user_id)
    if existing:
        raise GroupOperationError('您已經是該群組成員', 409)

    try:
        db.session.add(GroupMember(group_id=group.group_id, user_id=user_id))
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise GroupOperationError('加入群組失敗，請稍後再試', 500) from exc


def leave_group_for_user(group_id, user_id):
    member = get_group_member(group_id, user_id)
    if not member:
        raise GroupOperationError('您不是該群組成員', 404)

    try:
        db.session.delete(member)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise GroupOperationError('離開群組失敗，請稍後再試', 500) from exc


def list_group_members_payload(group_id):
    members = list_group_members_query(group_id)
    return [group_member_to_dict(member) for member in members]


def list_group_messages_for_member(group_id, user_id):
    if not is_group_member(group_id, user_id):
        raise GroupOperationError('您不是該群組成員', 403)

    messages = list_group_messages_query(group_id)
    return [group_message_to_dict(message) for message in messages]


def send_group_message_for_member(group_id, user_id, content):
    normalized_content = content.strip() if isinstance(content, str) else ''
    if not normalized_content:
        raise GroupOperationError('訊息內容不可為空', 400)

    if not is_group_member(group_id, user_id):
        raise GroupOperationError('您不是該群組成員', 403)

    new_message = Message(
        group_id=group_id,
        sender_id=user_id,
        content=normalized_content,
    )

    try:
        db.session.add(new_message)
        db.session.commit()
        return new_message.message_id
    except Exception as exc:
        db.session.rollback()
        raise GroupOperationError('發送訊息失敗，請稍後再試', 500) from exc


def group_snapshot_to_dict(snapshot):
    return {
        'snapshot_id': snapshot.snapshot_id,
        'group_id': snapshot.group_id,
        'summary': snapshot.summary_json,
        'created_by': snapshot.created_by,
        'created_at': _to_iso_z(snapshot.created_at),
        'source_count': snapshot.source_count,
        'model': snapshot.model,
        'provider': snapshot.provider,
        'metadata': snapshot.metadata_json or {},
    }


def _normalize_message_ids(raw_ids):
    normalized = []
    if isinstance(raw_ids, list):
        for item in raw_ids:
            try:
                normalized.append(int(item))
            except (TypeError, ValueError):
                continue
    # 依序去重
    return list(dict.fromkeys(normalized))


def _normalize_topics(raw_topics):
    topics = []
    if not isinstance(raw_topics, list):
        return topics

    for item in raw_topics:
        if isinstance(item, str):
            title = item.strip()
            message_ids = []
        elif isinstance(item, dict):
            title = str(item.get('title') or '').strip()
            message_ids = _normalize_message_ids(item.get('message_ids'))
        else:
            continue

        if not title:
            continue
        topics.append({'title': title, 'message_ids': message_ids})

    return topics


def _normalize_decisions(raw_decisions):
    decisions = []
    if not isinstance(raw_decisions, list):
        return decisions

    for item in raw_decisions:
        if isinstance(item, str):
            text = item.strip()
            message_ids = []
        elif isinstance(item, dict):
            text = str(item.get('text') or '').strip()
            message_ids = _normalize_message_ids(item.get('message_ids'))
        else:
            continue

        if not text:
            continue
        decisions.append({'text': text, 'message_ids': message_ids})

    return decisions


def _normalize_action_items(raw_actions):
    action_items = []
    if not isinstance(raw_actions, list):
        return action_items

    for item in raw_actions:
        if isinstance(item, str):
            text = item.strip()
            assignee = None
            message_ids = []
        elif isinstance(item, dict):
            text = str(item.get('text') or '').strip()
            assignee = item.get('assignee')
            message_ids = _normalize_message_ids(item.get('message_ids'))
        else:
            continue

        if not text:
            continue
        action_items.append({
            'text': text,
            'assignee': assignee,
            'message_ids': message_ids,
        })

    return action_items


def _normalize_blockers(raw_blockers):
    blockers = []
    if not isinstance(raw_blockers, list):
        return blockers

    for item in raw_blockers:
        if isinstance(item, str):
            text = item.strip()
            message_ids = []
        elif isinstance(item, dict):
            text = str(item.get('text') or '').strip()
            message_ids = _normalize_message_ids(item.get('message_ids'))
        else:
            continue

        if not text:
            continue
        blockers.append({'text': text, 'message_ids': message_ids})

    return blockers


def _normalize_notable_quotes(raw_quotes):
    notable_quotes = []
    if not isinstance(raw_quotes, list):
        return notable_quotes

    for item in raw_quotes:
        if isinstance(item, str):
            text = item.strip()
            message_id = None
        elif isinstance(item, dict):
            text = str(item.get('text') or '').strip()
            message_id = item.get('message_id')
            if message_id is None:
                message_ids = _normalize_message_ids(item.get('message_ids'))
                message_id = message_ids[0] if message_ids else None
            else:
                try:
                    message_id = int(message_id)
                except (TypeError, ValueError):
                    message_id = None
        else:
            continue

        if not text:
            continue
        notable_quotes.append({'text': text, 'message_id': message_id})

    return notable_quotes


def _normalize_snapshot_payload(payload):
    if not isinstance(payload, dict):
        raise GroupOperationError('AI 回傳格式錯誤，請稍後再試', 500)

    topics = _normalize_topics(payload.get('topics', []))
    decisions = _normalize_decisions(payload.get('decisions', []))
    action_items = _normalize_action_items(payload.get('action_items', payload.get('next_actions', [])))
    notable_quotes = _normalize_notable_quotes(payload.get('notable_quotes', []))
    blockers = _normalize_blockers(payload.get('blockers', []))

    # 兼容部分 provider 以「risks」輸出，收斂到 blockers。
    risks = payload.get('risks', [])
    if isinstance(risks, list):
        for risk in risks:
            text = str(risk).strip()
            if text:
                blockers.append({'text': text, 'message_ids': []})

    # 若模型沒有給 action_items，從 decisions 補最小可執行清單，避免輸出只剩長摘要。
    if not action_items:
        for decision in decisions[:3]:
            action_items.append({
                'text': f'跟進：{decision["text"]}',
                'assignee': None,
                'message_ids': decision.get('message_ids', []),
            })

    normalized = {
        'topics': topics,
        'decisions': decisions,
        'action_items': action_items,
        'blockers': blockers,
        'notable_quotes': notable_quotes,
    }

    return _finalize_snapshot_payload(normalized)


def _limit_and_trim_items(items, max_count, max_message_ids=3):
    limited = []
    for item in items[:max_count]:
        if isinstance(item, dict):
            cloned = dict(item)
            if 'message_ids' in cloned and isinstance(cloned['message_ids'], list):
                cloned['message_ids'] = cloned['message_ids'][:max_message_ids]
            limited.append(cloned)
    return limited


def _build_snapshot_digest(payload):
    action_items = payload.get('action_items', [])
    decisions = payload.get('decisions', [])
    blockers = payload.get('blockers', [])
    topics = payload.get('topics', [])

    if action_items:
        overview = f"目前優先：{action_items[0]['text']}"
    elif decisions:
        overview = f"目前共識：{decisions[0]['text']}"
    elif topics:
        overview = f"主要議題：{topics[0]['title']}"
    else:
        overview = '目前沒有明確可執行項目，建議先補充具體行動。'

    return {
        'overview': overview,
        'todo_for_user': [
            {
                'text': item.get('text'),
                'assignee': item.get('assignee'),
                'message_ids': item.get('message_ids', []),
            }
            for item in action_items[:5]
        ],
        'watch_out': blockers[:3],
        'decisions_brief': decisions[:3],
    }


def _finalize_snapshot_payload(payload):
    compacted = {
        'topics': _limit_and_trim_items(payload.get('topics', []), 3),
        'decisions': _limit_and_trim_items(payload.get('decisions', []), 5),
        'action_items': _limit_and_trim_items(payload.get('action_items', []), 5),
        'blockers': _limit_and_trim_items(payload.get('blockers', []), 3),
        'notable_quotes': _limit_and_trim_items(payload.get('notable_quotes', []), 5, max_message_ids=1),
    }

    compacted['digest'] = _build_snapshot_digest(compacted)
    return compacted


def parse_ai_snapshot_response(raw_text):
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise GroupOperationError('AI 回傳格式錯誤，請稍後再試', 500) from exc

    return _normalize_snapshot_payload(parsed)


def _merge_message_ids(existing_ids, incoming_ids):
    merged = list(existing_ids)
    seen = set(existing_ids)
    for value in incoming_ids:
        if value not in seen:
            merged.append(value)
            seen.add(value)
    return merged


def merge_chunk_summaries(chunk_summaries):
    topic_map = {}
    decision_map = {}
    action_map = {}
    blocker_map = {}
    quote_map = {}

    for summary in chunk_summaries:
        for topic in summary.get('topics', []):
            key = topic['title'].strip().lower()
            if key not in topic_map:
                topic_map[key] = {'title': topic['title'], 'message_ids': []}
            topic_map[key]['message_ids'] = _merge_message_ids(topic_map[key]['message_ids'], topic.get('message_ids', []))

        for decision in summary.get('decisions', []):
            key = decision['text'].strip().lower()
            if key not in decision_map:
                decision_map[key] = {'text': decision['text'], 'message_ids': []}
            decision_map[key]['message_ids'] = _merge_message_ids(decision_map[key]['message_ids'], decision.get('message_ids', []))

        for action in summary.get('action_items', []):
            key = (
                action['text'].strip().lower(),
                (action.get('assignee') or '').strip().lower() if isinstance(action.get('assignee'), str) else action.get('assignee'),
            )
            if key not in action_map:
                action_map[key] = {
                    'text': action['text'],
                    'assignee': action.get('assignee'),
                    'message_ids': [],
                }
            action_map[key]['message_ids'] = _merge_message_ids(action_map[key]['message_ids'], action.get('message_ids', []))

        for blocker in summary.get('blockers', []):
            key = blocker['text'].strip().lower()
            if key not in blocker_map:
                blocker_map[key] = {'text': blocker['text'], 'message_ids': []}
            blocker_map[key]['message_ids'] = _merge_message_ids(blocker_map[key]['message_ids'], blocker.get('message_ids', []))

        for quote in summary.get('notable_quotes', []):
            key = (quote['text'].strip().lower(), quote.get('message_id'))
            if key not in quote_map:
                quote_map[key] = {
                    'text': quote['text'],
                    'message_id': quote.get('message_id'),
                }

    merged = {
        'topics': list(topic_map.values()),
        'decisions': list(decision_map.values()),
        'action_items': list(action_map.values()),
        'blockers': list(blocker_map.values()),
        'notable_quotes': list(quote_map.values()),
    }

    return _finalize_snapshot_payload(merged)


def count_group_messages_for_snapshot(group_id, window_days):
    cutoff = _utcnow_naive() - timedelta(days=window_days)
    return (
        db.session.query(Message.message_id)
        .filter(Message.group_id == group_id)
        .filter(Message.created_at >= cutoff)
        .filter(Message.is_deleted.is_(False))
        .filter(Message.content.isnot(None))
        .count()
    )


def fetch_group_messages(group_id, window_days):
    cutoff = _utcnow_naive() - timedelta(days=window_days)
    rows = (
        db.session.query(
            Message.message_id,
            Message.content,
            Message.created_at,
            User.name.label('sender_name'),
        )
        .join(User, Message.sender_id == User.id)
        .filter(Message.group_id == group_id)
        .filter(Message.created_at >= cutoff)
        .filter(Message.is_deleted.is_(False))
        .filter(Message.content.isnot(None))
        .filter(Message.message_type != 'system')
        .order_by(Message.created_at.asc())
        .all()
    )

    payload = []
    for row in rows:
        text = row.content.strip() if isinstance(row.content, str) else ''
        if not text:
            continue
        payload.append({
            'message_id': row.message_id,
            'sender_name': row.sender_name,
            'content': text,
            'created_at': _to_iso_z(row.created_at),
        })

    return payload


def chunk_messages(messages, size):
    chunk_size = max(1, size)
    return [messages[index:index + chunk_size] for index in range(0, len(messages), chunk_size)]


def build_group_snapshot_system_prompt():
    return (
        '你是專案協作知識整理助手。重點是給出可執行下一步，避免冗長敘述。'
        '請輸出 JSON 物件，schema 必須為：'
        '{"topics":[{"title":str,"message_ids":[int]}],'
        '"decisions":[{"text":str,"message_ids":[int]}],'
        '"action_items":[{"text":str,"assignee":str|null,"message_ids":[int]}],'
        '"blockers":[{"text":str,"message_ids":[int]}],'
        '"notable_quotes":[{"text":str,"message_id":int|null}]}'
        '限制：topics<=3, decisions<=5, action_items<=5, blockers<=3。'
        '不要輸出 today/tomorrow 這類相對日期 due。'
    )


def build_chunk_prompt(chunk):
    lines = []
    for item in chunk:
        lines.append(
            f"[id={item['message_id']}] time={item['created_at']} sender={item['sender_name']} content={item['content']}"
        )
    return '請根據以下群組訊息整理知識快照：\n' + '\n'.join(lines)


def persist_snapshot(group_id, snapshot_payload, created_by, source_count, model, provider, metadata_json):
    snapshot = GroupAISnapshot(
        group_id=group_id,
        summary_json=snapshot_payload,
        created_by=created_by,
        source_count=source_count,
        model=model,
        provider=provider,
        metadata_json=metadata_json,
    )

    try:
        db.session.add(snapshot)
        db.session.commit()
        return group_snapshot_to_dict(snapshot)
    except Exception as exc:
        db.session.rollback()
        raise GroupOperationError('儲存群組快照失敗，請稍後再試', 500) from exc


def generate_group_snapshot(group_id, window_days=30, created_by=None, force=False):
    if not isinstance(window_days, int) or window_days <= 0:
        raise GroupOperationError('window_days 必須為正整數', 400)

    messages = fetch_group_messages(group_id, window_days)
    if not messages:
        raise GroupOperationError('最近沒有可摘要的群組訊息', 400)

    chunks = chunk_messages(messages, get_snapshot_chunk_size())

    try:
        provider = get_ai_provider()
    except RuntimeError as exc:
        raise GroupOperationError('AI 服務配置不完整，請檢查環境變數', 503) from exc

    chunk_summaries = []
    for chunk in chunks:
        try:
            raw = provider.generate_content(
                build_group_snapshot_system_prompt(),
                build_chunk_prompt(chunk),
                response_format='json',
            )
            parsed = parse_ai_snapshot_response(raw)
            chunk_summaries.append(parsed)
        except GroupOperationError:
            raise
        except RuntimeError as exc:
            raise GroupOperationError('AI 服務暫時不可用，請稍後再試', 503) from exc
        except Exception as exc:
            raise GroupOperationError('AI 生成失敗，請稍後再試', 500) from exc

    merged = merge_chunk_summaries(chunk_summaries)
    provider_name = os.getenv('AI_PROVIDER', 'gemini')
    model_name = getattr(provider, 'model', os.getenv('AI_MODEL', ''))
    metadata_json = {
        'window_days': window_days,
        'chunk_count': len(chunks),
        'force': bool(force),
    }

    return persist_snapshot(
        group_id=group_id,
        snapshot_payload=merged,
        created_by=created_by,
        source_count=len(messages),
        model=model_name,
        provider=provider_name,
        metadata_json=metadata_json,
    )


def get_latest_group_snapshot_for_member(group_id, user_id):
    if not is_group_member(group_id, user_id):
        raise GroupOperationError('您不是該群組成員', 403)

    snapshot = (
        GroupAISnapshot.query
        .filter_by(group_id=group_id)
        .order_by(GroupAISnapshot.created_at.desc())
        .first()
    )
    if not snapshot:
        raise GroupOperationError('尚無可用的群組快照', 404)

    return group_snapshot_to_dict(snapshot)


def should_enqueue_snapshot(source_count, async_requested=False):
    return bool(async_requested) or source_count > get_snapshot_async_threshold()


def _set_snapshot_job(job_id, patch_payload):
    with _snapshot_jobs_lock:
        if job_id not in _snapshot_jobs:
            return
        _snapshot_jobs[job_id].update(patch_payload)
        _snapshot_jobs[job_id]['updated_at'] = _to_iso_z(_utcnow_naive())


def _run_snapshot_job(app, job_id, group_id, user_id, window_days):
    _set_snapshot_job(job_id, {'status': 'running'})
    try:
        with app.app_context():
            snapshot = generate_group_snapshot(
                group_id=group_id,
                window_days=window_days,
                created_by=user_id,
            )
        _set_snapshot_job(job_id, {
            'status': 'completed',
            'snapshot': snapshot,
            'snapshot_id': snapshot.get('snapshot_id'),
            'error': None,
        })
    except GroupOperationError as exc:
        _set_snapshot_job(job_id, {
            'status': 'failed',
            'error': exc.message,
        })
    except Exception:
        _set_snapshot_job(job_id, {
            'status': 'failed',
            'error': '群組快照背景工作失敗',
        })


def enqueue_snapshot_job(app, group_id, user_id, window_days=30):
    job_id = uuid.uuid4().hex
    now_iso = _to_iso_z(_utcnow_naive())
    payload = {
        'job_id': job_id,
        'status': 'queued',
        'group_id': group_id,
        'requested_by': user_id,
        'window_days': window_days,
        'snapshot_id': None,
        'snapshot': None,
        'error': None,
        'created_at': now_iso,
        'updated_at': now_iso,
    }

    with _snapshot_jobs_lock:
        _snapshot_jobs[job_id] = payload

    _snapshot_executor.submit(_run_snapshot_job, app, job_id, group_id, user_id, window_days)
    return payload


def get_snapshot_job_status(job_id, requester_user_id=None):
    with _snapshot_jobs_lock:
        payload = dict(_snapshot_jobs.get(job_id, {}))

    if not payload:
        raise GroupOperationError('找不到指定的快照工作', 404)

    if requester_user_id is not None and payload.get('requested_by') != requester_user_id:
        raise GroupOperationError('無權查看此工作', 403)

    return payload
