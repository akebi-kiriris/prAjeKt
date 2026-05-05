from datetime import datetime

from models import db
from models.notification import Notification
from models.task import Task
from models.task_comment import TaskComment
from models.timeline import Timeline
from models.timeline_user import TimelineUser
from models.user import User
from services.timeline_service import (
    build_timeline_risk_analysis,
    build_weekly_report_for_timeline,
    trigger_timeline_risk_notifications,
)


def _create_user(email: str, username: str) -> User:
    user = User(
        name="Service Test User",
        username=username,
        email=email,
        password="hashed-password",
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_build_weekly_report_for_timeline_includes_summary_risks_and_comments(app):
    owner = _create_user("timeline-weekly-owner@example.com", "timeline_weekly_owner")
    member = _create_user("timeline-weekly-member@example.com", "timeline_weekly_member")

    timeline = Timeline(user_id=owner.id, name="Weekly Timeline")
    db.session.add(timeline)
    db.session.flush()
    db.session.add_all(
        [
            TimelineUser(timeline_id=timeline.id, user_id=owner.id, role=0),
            TimelineUser(timeline_id=timeline.id, user_id=member.id, role=1),
        ]
    )

    completed_task = Task(
        user_id=owner.id,
        timeline_id=timeline.id,
        name="完成任務",
        completed=True,
        status="completed",
        tags="前端,UI",
        end_date=datetime(2026, 4, 15),
        completed_at=datetime(2026, 4, 15, 10, 0, 0),
    )
    overdue_task = Task(
        user_id=member.id,
        timeline_id=timeline.id,
        name="逾期任務",
        completed=False,
        status="in_progress",
        end_date=datetime(2026, 4, 13),
    )
    future_task = Task(
        user_id=owner.id,
        timeline_id=timeline.id,
        name="下週任務",
        completed=False,
        status="pending",
        end_date=datetime(2026, 4, 25),
    )
    db.session.add_all([completed_task, overdue_task, future_task])
    db.session.flush()

    db.session.add(
        TaskComment(
            task_id=overdue_task.task_id,
            user_id=member.id,
            task_message="需要先解決 API 權限問題",
            created_at=datetime(2026, 4, 15, 15, 0, 0),
        )
    )
    db.session.commit()

    payload = build_weekly_report_for_timeline(
        timeline_id=timeline.id,
        start_date_raw="2026-04-14",
        end_date_raw="2026-04-20",
    )

    assert payload["timeline_id"] == timeline.id
    assert payload["overview"]["total_tasks"] == 3
    assert payload["overview"]["completed_tasks"] == 1
    assert payload["overview"]["comment_count"] == 1
    assert payload["overview"]["at_risk_tasks"] == 1
    assert payload["completed_tasks"][0]["task_id"] == completed_task.task_id
    assert any(item["task_id"] == overdue_task.task_id for item in payload["risk_items"])
    assert len(payload["next_actions"]) >= 1
    assert payload["recent_comments"][0]["task_name"] == overdue_task.name
    assert payload["analysis"]["weekly_goal_total"] == 1
    assert payload["analysis"]["weekly_goal_completed"] == 1
    assert payload["analysis"]["weekly_goal_completion_rate"] == 100.0
    assert payload["analysis"]["progress_signal"] in {"進度領先", "進度穩定", "進度落後"}
    assert "前端" in payload["analysis"]["top_tags"]


def test_build_timeline_risk_analysis_detects_cycle_and_missing_dependency(app):
    owner = _create_user("timeline-risk-owner@example.com", "timeline_risk_owner")

    timeline = Timeline(user_id=owner.id, name="Risk Timeline")
    db.session.add(timeline)
    db.session.flush()
    db.session.add(TimelineUser(timeline_id=timeline.id, user_id=owner.id, role=0))

    task_a = Task(
        user_id=owner.id,
        timeline_id=timeline.id,
        name="A",
        start_date=datetime(2026, 4, 10),
        end_date=datetime(2026, 4, 11),
        completed=False,
    )
    task_b = Task(
        user_id=owner.id,
        timeline_id=timeline.id,
        name="B",
        start_date=datetime(2026, 4, 12),
        end_date=datetime(2026, 4, 13),
        completed=False,
    )
    task_c = Task(
        user_id=owner.id,
        timeline_id=timeline.id,
        name="C",
        start_date=datetime(2026, 4, 14),
        end_date=datetime(2026, 4, 15),
        completed=False,
    )
    task_d = Task(
        user_id=owner.id,
        timeline_id=timeline.id,
        name="D",
        completed=False,
    )

    db.session.add_all([task_a, task_b, task_c, task_d])
    db.session.flush()

    task_a.depends_on_task_ids = [task_c.task_id]
    task_b.depends_on_task_ids = [task_a.task_id]
    task_c.depends_on_task_ids = [task_b.task_id, 999999]
    task_d.depends_on_task_ids = [task_b.task_id]
    db.session.commit()

    payload = build_timeline_risk_analysis(timeline.id)

    assert payload["message"] == "風險分析完成"
    assert payload["timeline_id"] == timeline.id
    assert payload["summary"]["total_tasks"] == 4
    assert payload["summary"]["critical_path_task_count"] >= 1
    assert len(payload["graph"]["nodes"]) == 4
    assert len(payload["critical_path"]) >= 1
    assert any(item["task_id"] == task_d.task_id for item in payload["risk_items"])

    warning_codes = {item["code"] for item in payload["warnings"]}
    assert "cycle_detected" in warning_codes
    assert "missing_dependency" in warning_codes


def test_trigger_timeline_risk_notifications_creates_notifications(app):
    owner = _create_user("timeline-risk-notify-owner@example.com", "timeline_risk_notify_owner")
    member = _create_user("timeline-risk-notify-member@example.com", "timeline_risk_notify_member")

    timeline = Timeline(user_id=owner.id, name="Risk Notify Timeline")
    db.session.add(timeline)
    db.session.flush()
    db.session.add_all(
        [
            TimelineUser(timeline_id=timeline.id, user_id=owner.id, role=0),
            TimelineUser(timeline_id=timeline.id, user_id=member.id, role=1),
        ]
    )

    blocker = Task(
        user_id=owner.id,
        timeline_id=timeline.id,
        name="關鍵阻塞任務",
        status="in_progress",
        start_date=datetime(2026, 4, 10),
        end_date=datetime(2026, 4, 11),
        completed=False,
    )
    follower = Task(
        user_id=member.id,
        timeline_id=timeline.id,
        name="後續驗收",
        status="pending",
        start_date=datetime(2026, 4, 12),
        end_date=datetime(2026, 4, 13),
        completed=False,
        depends_on_task_ids=[],
    )
    db.session.add_all([blocker, follower])
    db.session.flush()
    follower.depends_on_task_ids = [blocker.task_id]
    db.session.commit()

    payload = trigger_timeline_risk_notifications(timeline.id)

    assert payload["timeline_id"] == timeline.id
    assert payload["notified_user_count"] == 2
    assert payload["risk_item_count"] >= 1

    notifications = Notification.query.filter(Notification.type == "risk_alert").all()
    assert len(notifications) >= 2
