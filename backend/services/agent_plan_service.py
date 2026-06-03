from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock
from uuid import uuid4


PlanStatus = str


@dataclass
class AgentPlanRecord:
    plan_id: str
    user_id: int
    goal: str
    context: dict
    approved_tool_payloads: dict[str, dict]
    pending_tools: list[str]
    summary: str
    steps_preview: list[str]
    risk_notes: list[str]
    status: PlanStatus
    created_at: datetime
    expires_at: datetime
    rejected_reason: str | None = None
    execution_id: str | None = None
    proposal_source: str = "rule_fallback"
    proposal_reason: str | None = None


class AgentPlanStore:
    """In-memory plan store for phase 9.4 plan-confirm-execute workflow."""

    def __init__(self, ttl_minutes: int = 15) -> None:
        self._ttl_minutes = ttl_minutes
        self._lock = Lock()
        self._plans: dict[str, AgentPlanRecord] = {}

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _build_plan_id(self) -> str:
        return f"plan_{uuid4().hex}"

    def _build_execution_id(self) -> str:
        return f"exec_{uuid4().hex}"

    def _expire_unsafe(self, now: datetime) -> None:
        for plan in self._plans.values():
            if plan.status == "planned" and plan.expires_at <= now:
                plan.status = "expired"

    def create_plan(
        self,
        *,
        user_id: int,
        goal: str,
        context: dict,
        pending_tools: list[str],
        approved_tool_payloads: dict[str, dict] | None = None,
        summary: str,
        steps_preview: list[str],
        risk_notes: list[str],
        proposal_source: str = "rule_fallback",
        proposal_reason: str | None = None,
    ) -> AgentPlanRecord:
        now = self._now()
        record = AgentPlanRecord(
            plan_id=self._build_plan_id(),
            user_id=user_id,
            goal=goal,
            context=context,
            approved_tool_payloads=approved_tool_payloads or {},
            pending_tools=pending_tools,
            summary=summary,
            steps_preview=steps_preview,
            risk_notes=risk_notes,
            status="planned",
            created_at=now,
            expires_at=now + timedelta(minutes=self._ttl_minutes),
            proposal_source=proposal_source,
            proposal_reason=proposal_reason,
        )
        with self._lock:
            self._expire_unsafe(now)
            self._plans[record.plan_id] = record
        return record

    def get_plan(self, plan_id: str, *, user_id: int) -> AgentPlanRecord | None:
        now = self._now()
        with self._lock:
            self._expire_unsafe(now)
            plan = self._plans.get(plan_id)
            if not plan or plan.user_id != user_id:
                return None
            return plan

    def reject_plan(self, plan_id: str, *, user_id: int, reason: str | None = None) -> AgentPlanRecord | None:
        now = self._now()
        with self._lock:
            self._expire_unsafe(now)
            plan = self._plans.get(plan_id)
            if not plan or plan.user_id != user_id:
                return None
            if plan.status != "planned":
                return plan
            plan.status = "rejected"
            plan.rejected_reason = reason
            return plan

    def mark_executing(self, plan_id: str, *, user_id: int) -> AgentPlanRecord | None:
        now = self._now()
        with self._lock:
            self._expire_unsafe(now)
            plan = self._plans.get(plan_id)
            if not plan or plan.user_id != user_id:
                return None
            if plan.status != "planned":
                return None
            plan.status = "executing"
            plan.execution_id = self._build_execution_id()
            return plan

    def mark_executed(self, plan_id: str, *, user_id: int, succeeded: bool) -> AgentPlanRecord | None:
        now = self._now()
        with self._lock:
            self._expire_unsafe(now)
            plan = self._plans.get(plan_id)
            if not plan or plan.user_id != user_id:
                return None
            if plan.status != "executing":
                return plan
            plan.status = "succeeded" if succeeded else "failed"
            return plan


agent_plan_store = AgentPlanStore(ttl_minutes=15)
