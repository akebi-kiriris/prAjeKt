from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from threading import Lock
from time import perf_counter
from typing import Any
from uuid import uuid4


def build_agent_request_id() -> str:
    return f"req_{uuid4().hex}"


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class AgentTraceService:
    """Lightweight in-memory trace store for plan/execute/replan flow."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._traces: dict[str, dict[str, Any]] = {}

    def start_trace(
        self,
        request_id: str,
        *,
        route: str,
        user_id: int | None = None,
        plan_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        now_iso = _utc_now_iso()
        with self._lock:
            trace = self._traces.get(request_id)
            if trace is None:
                trace = {
                    "request_id": request_id,
                    "user_id": user_id,
                    "plan_id": plan_id,
                    "routes": [route],
                    "status": "running",
                    "started_at": now_iso,
                    "updated_at": now_iso,
                    "finished_at": None,
                    "duration_ms": None,
                    "metadata": dict(metadata or {}),
                    "events": [],
                }
                self._traces[request_id] = trace
                return

            if route not in trace["routes"]:
                trace["routes"].append(route)
            if user_id is not None:
                trace["user_id"] = user_id
            if plan_id:
                trace["plan_id"] = plan_id
            if metadata:
                trace["metadata"].update(metadata)
            trace["status"] = "running"
            trace["updated_at"] = now_iso

    def append_event(
        self,
        request_id: str,
        *,
        event_type: str,
        step_name: str,
        status: str | None = None,
        duration_ms: int | None = None,
        error_code: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        now_iso = _utc_now_iso()
        event = {
            "event_type": event_type,
            "step_name": step_name,
            "status": status,
            "duration_ms": duration_ms,
            "error_code": error_code,
            "detail": dict(detail or {}),
            "timestamp": now_iso,
        }
        with self._lock:
            trace = self._traces.get(request_id)
            if trace is None:
                return
            trace["events"].append(event)
            trace["updated_at"] = now_iso

    def finish_trace(
        self,
        request_id: str,
        *,
        status: str,
        duration_ms: int | None = None,
        error_code: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        finished_at = _utc_now_iso()
        with self._lock:
            trace = self._traces.get(request_id)
            if trace is None:
                return
            trace["status"] = status
            trace["finished_at"] = finished_at
            trace["updated_at"] = finished_at
            if duration_ms is not None:
                trace["duration_ms"] = duration_ms
            if error_code:
                trace["error_code"] = error_code
            if detail:
                trace["metadata"].update(detail)

    def get_trace(self, request_id: str) -> dict[str, Any] | None:
        with self._lock:
            trace = self._traces.get(request_id)
            return deepcopy(trace) if trace is not None else None

    def clear(self) -> None:
        with self._lock:
            self._traces.clear()


def duration_ms_since(started_at: float) -> int:
    return int((perf_counter() - started_at) * 1000)


agent_trace_service = AgentTraceService()
