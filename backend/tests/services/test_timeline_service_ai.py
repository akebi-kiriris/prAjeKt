from datetime import datetime

import pytest

from models import db
from models.task import Task
from models.timeline import Timeline
from models.user import User
from services.timeline_service import (
    TimelineAIGenerationError,
    batch_create_tasks_for_timeline,
    find_unknown_fields as timeline_find_unknown_fields,
    generate_timeline_tasks_with_ai,
)



def test_timeline_service_find_unknown_fields_sorted(user_factory):
    unknown = timeline_find_unknown_fields(
        {"name": "Timeline", "remark": "r", "x": 1},
        {"name", "remark"},
    )
    assert unknown == ["x"]


def test_generate_timeline_tasks_with_ai_missing_api_key(app, monkeypatch, user_factory):
    owner = user_factory("timeline-ai-service-owner@example.com", "timeline_ai_service_owner")
    timeline = Timeline(user_id=owner.id, name="AI Service Timeline")
    db.session.add(timeline)
    db.session.commit()

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(TimelineAIGenerationError) as excinfo:
        generate_timeline_tasks_with_ai(
            timeline_id=timeline.id,
            project_name="AI Service Project",
            description="service layer prompt",
        )

    assert excinfo.value.code == "missing_api_key"


def test_generate_timeline_tasks_with_ai_success_and_json_decode_error(app, monkeypatch, user_factory):
    owner = user_factory("timeline-ai-service-ok@example.com", "timeline_ai_service_ok")
    timeline = Timeline(user_id=owner.id, name="AI Service OK Timeline")
    db.session.add(timeline)
    db.session.flush()

    existing_task = Task(
        user_id=owner.id,
        timeline_id=timeline.id,
        name="existing service task",
        start_date=datetime(2026, 4, 1),
        end_date=datetime(2026, 4, 5),
    )
    db.session.add(existing_task)
    db.session.commit()

    from unittest.mock import MagicMock

    mock_llm = MagicMock()
    mock_generate_tasks = MagicMock(
        return_value=[
            {
                "name": "service ai task",
                "priority": 1,
                "estimated_days": 2,
                "task_remark": "from chain",
                "depends_on_task_refs": ["existing service task"],
            }
        ]
    )

    monkeypatch.setattr("services.timeline_service.get_default_llm", MagicMock(return_value=mock_llm))
    monkeypatch.setattr("services.timeline_service.generate_timeline_tasks_from_context", mock_generate_tasks)

    payload = generate_timeline_tasks_with_ai(
        timeline_id=timeline.id,
        project_name="AI Service Project",
        description="service layer prompt",
    )

    assert payload["existingCount"] == 1
    assert payload["generatedCount"] == 1
    assert len(payload["tasks"]) == 2
    assert payload["tasks"][1]["name"] == "service ai task"
    assert payload["tasks"][1]["isExisting"] is False
    assert payload["tasks"][1]["depends_on_task_refs"] == ["existing service task"]

    mock_generate_tasks_error = MagicMock(side_effect=ValueError("Invalid JSON from LLM"))
    monkeypatch.setattr("services.timeline_service.generate_timeline_tasks_from_context", mock_generate_tasks_error)

    with pytest.raises(TimelineAIGenerationError) as excinfo:
        generate_timeline_tasks_with_ai(
            timeline_id=timeline.id,
            project_name="AI Service Project",
            description="service layer prompt",
        )

    assert excinfo.value.code == "generation_failed"


def test_generate_timeline_tasks_with_ai_auto_fallback_dependency_chain(app, monkeypatch, user_factory):
    owner = user_factory("timeline-ai-service-chain@example.com", "timeline_ai_service_chain")
    timeline = Timeline(user_id=owner.id, name="AI Service Chain Timeline")
    db.session.add(timeline)
    db.session.commit()

    from unittest.mock import MagicMock

    mock_llm = MagicMock()
    mock_generate_tasks = MagicMock(
        return_value=[
            {"name": "需求釐清", "priority": 1, "estimated_days": 1, "task_remark": "step1"},
            {"name": "API 開發", "priority": 1, "estimated_days": 2, "task_remark": "step2"},
            {"name": "前端串接", "priority": 2, "estimated_days": 2, "task_remark": "step3"},
        ]
    )

    monkeypatch.setattr("services.timeline_service.get_default_llm", MagicMock(return_value=mock_llm))
    monkeypatch.setattr("services.timeline_service.generate_timeline_tasks_from_context", mock_generate_tasks)

    payload = generate_timeline_tasks_with_ai(
        timeline_id=timeline.id,
        project_name="AI Service Chain Project",
        description="service layer prompt",
    )

    generated_tasks = [task for task in payload["tasks"] if not task.get("isExisting")]
    assert len(generated_tasks) == 3
    assert generated_tasks[0]["depends_on_task_refs"] == []
    assert generated_tasks[1]["depends_on_task_refs"] == ["需求釐清"]
    assert generated_tasks[2]["depends_on_task_refs"] == ["API 開發"]


def test_batch_create_tasks_for_timeline_partial_selection_dependency_fallback(app, user_factory):
    owner = user_factory("timeline-service-batch-partial@example.com", "timeline_service_batch_partial")

    timeline = Timeline(user_id=owner.id, name="Service batch partial timeline")
    db.session.add(timeline)
    db.session.commit()

    payload = batch_create_tasks_for_timeline(
        timeline_id=timeline.id,
        user_id=owner.id,
        task_payloads=[
            {
                "isExisting": False,
                "name": "任務1",
                "priority": 2,
                "status": "pending",
                "estimated_days": 1,
                "task_remark": "chain 1",
                "depends_on_task_refs": [],
            },
            {
                "isExisting": False,
                "name": "任務2",
                "priority": 2,
                "status": "pending",
                "estimated_days": 1,
                "task_remark": "chain 2",
                "depends_on_task_refs": ["任務1"],
            },
            {
                "isExisting": False,
                "name": "任務4",
                "priority": 2,
                "status": "pending",
                "estimated_days": 1,
                "task_remark": "chain 4",
                "depends_on_task_refs": ["任務3"],
            },
            {
                "isExisting": False,
                "name": "任務5",
                "priority": 2,
                "status": "pending",
                "estimated_days": 1,
                "task_remark": "chain 5",
                "depends_on_task_refs": ["任務4"],
            },
        ],
    )

    assert payload["created"] == 4
    assert payload["ignored_dependency_refs"] == 1
    assert payload["ignored_dependency_ids"] == 0

    task_1 = Task.query.filter_by(timeline_id=timeline.id, name="任務1").first()
    task_2 = Task.query.filter_by(timeline_id=timeline.id, name="任務2").first()
    task_4 = Task.query.filter_by(timeline_id=timeline.id, name="任務4").first()
    task_5 = Task.query.filter_by(timeline_id=timeline.id, name="任務5").first()

    assert task_1 is not None
    assert task_2 is not None
    assert task_4 is not None
    assert task_5 is not None

    assert task_1.depends_on_task_ids == []
    assert task_2.depends_on_task_ids == [task_1.task_id]
    assert task_4.depends_on_task_ids == []
    assert task_5.depends_on_task_ids == [task_4.task_id]


def test_batch_create_tasks_for_timeline_ignores_unresolvable_dependency_ids(app, user_factory):
    owner = user_factory("timeline-service-batch-ids@example.com", "timeline_service_batch_ids")

    timeline = Timeline(user_id=owner.id, name="Service batch ids timeline")
    db.session.add(timeline)
    db.session.flush()

    keep_task = Task(user_id=owner.id, timeline_id=timeline.id, name="keep task")
    db.session.add(keep_task)
    db.session.commit()

    payload = batch_create_tasks_for_timeline(
        timeline_id=timeline.id,
        user_id=owner.id,
        task_payloads=[
            {
                "task_id": keep_task.task_id,
                "isExisting": True,
                "name": "keep task",
            },
            {
                "isExisting": False,
                "name": "new task with mixed deps",
                "priority": 1,
                "status": "pending",
                "estimated_days": 2,
                "task_remark": "mixed dep ids",
                "depends_on_task_ids": [keep_task.task_id, 999999],
            },
        ],
    )

    created = Task.query.filter_by(timeline_id=timeline.id, name="new task with mixed deps").first()

    assert created is not None
    assert created.depends_on_task_ids == [keep_task.task_id]
    assert payload["ignored_dependency_refs"] == 0
    assert payload["ignored_dependency_ids"] == 1
