from werkzeug.security import generate_password_hash
import pytest

from models import db
from models.group import Group, GroupMember
from models.message import Message
from models.user import User
from services.group_service import (
    GroupOperationError,
    chunk_messages,
    generate_group_snapshot,
    get_latest_group_snapshot_for_member,
    merge_chunk_summaries,
    should_enqueue_snapshot,
)
import services.group_service as group_service_module


def _create_user(email: str, username: str) -> User:
    user = User(
        name="Group Snapshot Service User",
        username=username,
        email=email,
        password=generate_password_hash("Password123!"),
    )
    db.session.add(user)
    db.session.commit()
    return user


def _create_group_with_owner(owner: User) -> Group:
    group = Group(
        group_name="Snapshot Service Group",
        group_type="task",
        group_inviteCode="654321",
        created_by=owner.id,
    )
    db.session.add(group)
    db.session.flush()
    db.session.add(GroupMember(group_id=group.group_id, user_id=owner.id))
    db.session.commit()
    return group


def test_chunk_messages_splits_by_size(app):
    messages = [
        {"message_id": 1, "content": "a"},
        {"message_id": 2, "content": "b"},
        {"message_id": 3, "content": "c"},
    ]

    chunks = chunk_messages(messages, 2)

    assert len(chunks) == 2
    assert len(chunks[0]) == 2
    assert len(chunks[1]) == 1


def test_merge_chunk_summaries_deduplicates(app):
    merged = merge_chunk_summaries(
        [
            {
                "topics": [{"title": "API", "message_ids": [1]}],
                "decisions": [{"text": "先做後端", "message_ids": [1]}],
                "action_items": [{"text": "補測試", "assignee": "A", "message_ids": [1]}],
                "blockers": [{"text": "等待環境穩定", "message_ids": [1]}],
                "notable_quotes": [{"text": "先做後端", "message_id": 1}],
            },
            {
                "topics": [{"title": "API", "message_ids": [2]}],
                "decisions": [{"text": "先做後端", "message_ids": [2]}],
                "action_items": [{"text": "補測試", "assignee": "A", "message_ids": [2]}],
                "blockers": [{"text": "等待環境穩定", "message_ids": [2]}],
                "notable_quotes": [{"text": "先做後端", "message_id": 1}],
            },
        ]
    )

    assert len(merged["topics"]) == 1
    assert merged["topics"][0]["message_ids"] == [1, 2]
    assert len(merged["decisions"]) == 1
    assert merged["decisions"][0]["message_ids"] == [1, 2]
    assert len(merged["action_items"]) == 1
    assert merged["action_items"][0]["message_ids"] == [1, 2]
    assert len(merged["blockers"]) == 1
    assert merged["blockers"][0]["message_ids"] == [1, 2]
    assert len(merged["notable_quotes"]) == 1
    assert merged["digest"]["todo_for_user"][0]["text"] == "補測試"


def test_generate_group_snapshot_success_and_latest(app, monkeypatch):
    owner = _create_user("group-snapshot-service-owner@example.com", "group_snapshot_service_owner")
    group = _create_group_with_owner(owner)

    db.session.add_all([
        Message(group_id=group.group_id, sender_id=owner.id, content="先完成 API 設計"),
        Message(group_id=group.group_id, sender_id=owner.id, content="明天補上測試"),
    ])
    db.session.commit()

    monkeypatch.setenv("SNAPSHOT_CHUNK_SIZE", "1")

    class FakeProvider:
        model = "fake-snapshot-model"

        def __init__(self):
            self.index = 0

        def generate_content(self, system_prompt, user_message, response_format="json"):
            self.index += 1
            if self.index == 1:
                return (
                    '{"topics":[{"title":"API","message_ids":[1]}],'
                    '"decisions":[{"text":"先做 API","message_ids":[1]}],'
                    '"action_items":[{"text":"補上測試","assignee":"Owner","message_ids":[1]}],'
                    '"blockers":[{"text":"等待 API 合併","message_ids":[1]}],'
                    '"notable_quotes":[{"text":"先完成 API 設計","message_id":1}]}'
                )
            return (
                '{"topics":[{"title":"API","message_ids":[2]}],'
                '"decisions":[{"text":"先做 API","message_ids":[2]}],'
                '"action_items":[{"text":"補上測試","assignee":"Owner","message_ids":[2]}],'
                '"notable_quotes":[{"text":"明天補上測試","message_id":2}]}'
            )

    monkeypatch.setattr(group_service_module, "get_ai_provider", lambda: FakeProvider())

    snapshot = generate_group_snapshot(group_id=group.group_id, window_days=30, created_by=owner.id)

    assert snapshot["group_id"] == group.group_id
    assert snapshot["source_count"] == 2
    assert snapshot["summary"]["topics"][0]["title"] == "API"
    assert snapshot["summary"]["topics"][0]["message_ids"] == [1, 2]
    assert snapshot["summary"]["digest"]["todo_for_user"][0]["text"] == "補上測試"
    assert snapshot["summary"]["digest"]["watch_out"][0]["text"] == "等待 API 合併"

    latest = get_latest_group_snapshot_for_member(group.group_id, owner.id)
    assert latest["snapshot_id"] == snapshot["snapshot_id"]


def test_generate_group_snapshot_no_messages(app):
    owner = _create_user("group-snapshot-service-empty@example.com", "group_snapshot_service_empty")
    group = _create_group_with_owner(owner)

    with pytest.raises(GroupOperationError) as excinfo:
        generate_group_snapshot(group_id=group.group_id, window_days=30, created_by=owner.id)

    assert excinfo.value.status_code == 400


def test_should_enqueue_snapshot_threshold_logic(app):
    assert should_enqueue_snapshot(source_count=10, async_requested=False) is False
    assert should_enqueue_snapshot(source_count=9999, async_requested=False) is True
    assert should_enqueue_snapshot(source_count=1, async_requested=True) is True
