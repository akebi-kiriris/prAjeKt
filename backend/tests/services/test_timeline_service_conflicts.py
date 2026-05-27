from datetime import datetime

import pytest

from models import db
from models.task import Task
from models.task_user import TaskUser
from models.timeline import Timeline
from models.timeline_user import TimelineUser
from models.user import User
from services.timeline_service import TimelineOperationError, check_timeline_task_conflicts
import services.timeline_service as timeline_service_module



def test_check_timeline_task_conflicts_detects_overlap_and_suggestion(app, user_factory):
    owner = user_factory("timeline-conflict-owner@example.com", "timeline_conflict_owner")

    timeline = Timeline(user_id=owner.id, name="Conflict Timeline")
    db.session.add(timeline)
    db.session.flush()
    db.session.add(TimelineUser(timeline_id=timeline.id, user_id=owner.id, role=0))

    existing_task = Task(
        user_id=owner.id,
        timeline_id=timeline.id,
        name="既有任務",
        status="in_progress",
        start_date=datetime(2026, 4, 10),
        end_date=datetime(2026, 4, 12),
    )
    db.session.add(existing_task)
    db.session.flush()
    db.session.add(TaskUser(task_id=existing_task.task_id, user_id=owner.id, role=0))
    db.session.commit()

    conflict_payload = check_timeline_task_conflicts(
        timeline_id=timeline.id,
        payload={
            "name": "新任務",
            "start_date": "2026-04-11",
            "end_date": "2026-04-13",
            "assignee_user_id": owner.id,
        },
        actor_user_id=owner.id,
    )

    assert conflict_payload["has_conflict"] is True
    assert conflict_payload["conflict_count"] == 1
    assert conflict_payload["conflicts"][0]["task_id"] == existing_task.task_id
    assert conflict_payload["conflicts"][0]["same_assignee"] is True
    assert conflict_payload["suggestion"]["start_date"] == "2026-04-13"
    assert conflict_payload["suggestion"]["end_date"] == "2026-04-15"
    assert conflict_payload["cross_project_conflict_count"] == 0
    assert conflict_payload["workload_overload_count"] == 0
    assert conflict_payload["workload_overload_days"] == []

    with pytest.raises(TimelineOperationError) as excinfo:
        check_timeline_task_conflicts(
            timeline_id=timeline.id,
            payload={"name": "缺少截止日"},
            actor_user_id=owner.id,
        )
    assert excinfo.value.status_code == 400


def test_check_timeline_task_conflicts_skips_ai_suggestion_when_not_enabled(app, monkeypatch, user_factory):
    monkeypatch.delenv("CONFLICT_CHECK_ENABLE_AI_SUGGESTION", raising=False)

    owner = user_factory("timeline-conflict-ai-off-owner@example.com", "timeline_conflict_ai_off_owner")

    timeline = Timeline(user_id=owner.id, name="Conflict AI Off Timeline")
    db.session.add(timeline)
    db.session.flush()
    db.session.add(TimelineUser(timeline_id=timeline.id, user_id=owner.id, role=0))

    existing_task = Task(
        user_id=owner.id,
        timeline_id=timeline.id,
        name="既有任務",
        status="in_progress",
        start_date=datetime(2026, 4, 10),
        end_date=datetime(2026, 4, 12),
    )
    db.session.add(existing_task)
    db.session.flush()
    db.session.add(TaskUser(task_id=existing_task.task_id, user_id=owner.id, role=0))
    db.session.commit()

    called = {"value": False}

    def _fake_generate_conflict_suggestion(**kwargs):
        called["value"] = True
        return "AI 建議"

    monkeypatch.setattr(
        timeline_service_module,
        "generate_conflict_suggestion",
        _fake_generate_conflict_suggestion,
    )
    monkeypatch.setattr(
        timeline_service_module,
        "get_default_llm",
        lambda **kwargs: object(),
    )

    conflict_payload = check_timeline_task_conflicts(
        timeline_id=timeline.id,
        payload={
            "name": "新任務",
            "start_date": "2026-04-11",
            "end_date": "2026-04-13",
            "assignee_user_id": owner.id,
        },
        actor_user_id=owner.id,
    )

    assert conflict_payload["has_conflict"] is True
    assert conflict_payload["ai_suggestion"] == ""
    assert called["value"] is False


def test_check_timeline_task_conflicts_allows_ai_suggestion_when_payload_enables_it(app, monkeypatch, user_factory):
    monkeypatch.delenv("CONFLICT_CHECK_ENABLE_AI_SUGGESTION", raising=False)

    owner = user_factory("timeline-conflict-ai-on-owner@example.com", "timeline_conflict_ai_on_owner")

    timeline = Timeline(user_id=owner.id, name="Conflict AI On Timeline")
    db.session.add(timeline)
    db.session.flush()
    db.session.add(TimelineUser(timeline_id=timeline.id, user_id=owner.id, role=0))

    existing_task = Task(
        user_id=owner.id,
        timeline_id=timeline.id,
        name="既有任務",
        status="in_progress",
        start_date=datetime(2026, 4, 10),
        end_date=datetime(2026, 4, 12),
    )
    db.session.add(existing_task)
    db.session.flush()
    db.session.add(TaskUser(task_id=existing_task.task_id, user_id=owner.id, role=0))
    db.session.commit()

    called = {"value": False}
    captured_kwargs = {}

    def _fake_generate_conflict_suggestion(**kwargs):
        called["value"] = True
        captured_kwargs.update(kwargs)
        return "AI 建議"

    monkeypatch.setattr(
        timeline_service_module,
        "generate_conflict_suggestion",
        _fake_generate_conflict_suggestion,
    )
    monkeypatch.setattr(
        timeline_service_module,
        "get_default_llm",
        lambda **kwargs: object(),
    )

    conflict_payload = check_timeline_task_conflicts(
        timeline_id=timeline.id,
        payload={
            "name": "新任務",
            "start_date": "2026-04-11",
            "end_date": "2026-04-13",
            "assignee_user_id": owner.id,
            "include_ai_suggestion": True,
        },
        actor_user_id=owner.id,
    )

    assert conflict_payload["has_conflict"] is True
    assert conflict_payload["ai_suggestion"] == "AI 建議"
    assert conflict_payload["include_ai_suggestion"] is True
    assert called["value"] is True
    assert isinstance(captured_kwargs.get("risk_context_text"), str)
    assert "critical_path" in captured_kwargs["risk_context_text"]
    assert "impact_days" in captured_kwargs["risk_context_text"]


def test_check_timeline_task_conflicts_ignores_completed_tasks_in_same_timeline(app, user_factory):
    owner = user_factory("timeline-completed-owner@example.com", "timeline_completed_owner")

    timeline = Timeline(user_id=owner.id, name="Completed Conflict Timeline")
    db.session.add(timeline)
    db.session.flush()
    db.session.add(TimelineUser(timeline_id=timeline.id, user_id=owner.id, role=0))

    completed_task = Task(
        user_id=owner.id,
        timeline_id=timeline.id,
        name="已完成任務",
        status="completed",
        completed=True,
        start_date=datetime(2026, 4, 10),
        end_date=datetime(2026, 4, 12),
    )
    db.session.add(completed_task)
    db.session.flush()
    db.session.add(TaskUser(task_id=completed_task.task_id, user_id=owner.id, role=0))
    db.session.commit()

    conflict_payload = check_timeline_task_conflicts(
        timeline_id=timeline.id,
        payload={
            "name": "新任務",
            "start_date": "2026-04-11",
            "end_date": "2026-04-13",
            "assignee_user_id": owner.id,
        },
        actor_user_id=owner.id,
    )

    assert conflict_payload["has_conflict"] is False
    assert conflict_payload["conflict_count"] == 0
    assert conflict_payload["conflicts"] == []
    assert conflict_payload["workload_overload_count"] == 0


def test_check_timeline_task_conflicts_rejects_non_timeline_member_assignee(app, user_factory):
    owner = user_factory("timeline-assignee-owner@example.com", "timeline_assignee_owner")
    outsider = user_factory("timeline-assignee-outsider@example.com", "timeline_assignee_outsider")

    timeline = Timeline(user_id=owner.id, name="Assignee Validation Timeline")
    db.session.add(timeline)
    db.session.flush()
    db.session.add(TimelineUser(timeline_id=timeline.id, user_id=owner.id, role=0))
    db.session.commit()

    with pytest.raises(TimelineOperationError) as excinfo:
        check_timeline_task_conflicts(
            timeline_id=timeline.id,
            payload={
                "name": "新任務",
                "start_date": "2026-04-11",
                "end_date": "2026-04-12",
                "assignee_user_id": outsider.id,
            },
            actor_user_id=owner.id,
        )

    assert excinfo.value.status_code == 400
    assert "assignee_user_id 必須是專案成員" in excinfo.value.message


def test_check_timeline_task_conflicts_includes_cross_project_and_workload_overload(app, monkeypatch, user_factory):
    monkeypatch.setenv("ASSIGNEE_DAILY_OVERLOAD_THRESHOLD", "1")

    owner = user_factory("timeline-cross-owner@example.com", "timeline_cross_owner")

    main_timeline = Timeline(user_id=owner.id, name="Main Timeline")
    legacy_timeline = Timeline(user_id=owner.id, name="Legacy Timeline")
    db.session.add_all([main_timeline, legacy_timeline])
    db.session.flush()
    db.session.add_all(
        [
            TimelineUser(timeline_id=main_timeline.id, user_id=owner.id, role=0),
            TimelineUser(timeline_id=legacy_timeline.id, user_id=owner.id, role=0),
        ]
    )

    legacy_task = Task(
        user_id=owner.id,
        timeline_id=legacy_timeline.id,
        name="舊專案排程",
        status="in_progress",
        start_date=datetime(2026, 4, 11),
        end_date=datetime(2026, 4, 13),
        completed=False,
    )
    db.session.add(legacy_task)
    db.session.commit()

    conflict_payload = check_timeline_task_conflicts(
        timeline_id=main_timeline.id,
        payload={
            "name": "新專案任務",
            "start_date": "2026-04-11",
            "end_date": "2026-04-12",
            "assignee_user_id": owner.id,
        },
        actor_user_id=owner.id,
    )

    assert conflict_payload["has_conflict"] is True
    assert conflict_payload["cross_project_conflict_count"] >= 1
    assert any(item.get("is_cross_project") is True for item in conflict_payload["conflicts"])
    assert any(item.get("timeline_name") == "Legacy Timeline" for item in conflict_payload["conflicts"])
    assert conflict_payload["workload_overload_count"] >= 1
    assert conflict_payload["workload_overload_days"][0]["projected_task_count"] >= 2


def test_check_timeline_task_conflicts_masks_names_for_other_assignee(app, monkeypatch, user_factory):
    monkeypatch.setenv("ASSIGNEE_DAILY_OVERLOAD_THRESHOLD", "1")

    owner = user_factory("timeline-mask-owner@example.com", "timeline_mask_owner")
    member = user_factory("timeline-mask-member@example.com", "timeline_mask_member")

    timeline = Timeline(user_id=owner.id, name="Mask Timeline")
    db.session.add(timeline)
    db.session.flush()
    db.session.add_all(
        [
            TimelineUser(timeline_id=timeline.id, user_id=owner.id, role=0),
            TimelineUser(timeline_id=timeline.id, user_id=member.id, role=1),
        ]
    )

    existing_task = Task(
        user_id=owner.id,
        timeline_id=timeline.id,
        name="不可外露任務名稱",
        status="in_progress",
        start_date=datetime(2026, 4, 12),
        end_date=datetime(2026, 4, 14),
        completed=False,
    )
    db.session.add(existing_task)
    db.session.flush()
    db.session.add(TaskUser(task_id=existing_task.task_id, user_id=owner.id, role=0))
    db.session.add(TaskUser(task_id=existing_task.task_id, user_id=member.id, role=1))
    db.session.commit()

    conflict_payload = check_timeline_task_conflicts(
        timeline_id=timeline.id,
        payload={
            "name": "新指派任務",
            "start_date": "2026-04-13",
            "end_date": "2026-04-13",
            "assignee_user_id": member.id,
            "priority": 3,
        },
        actor_user_id=owner.id,
    )

    assert conflict_payload["has_conflict"] is True
    assert conflict_payload["is_task_name_redacted"] is True
    assert conflict_payload["assignee_name"] == member.name
    assert all("隱私保護" in item["name"] for item in conflict_payload["conflicts"])
    if conflict_payload["workload_overload_days"]:
        assert all(item["sample_tasks"] == [] for item in conflict_payload["workload_overload_days"])
