from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from contracts.shared_fields import (
    parse_int_or_none,
    validate_iso_datetime_text,
    validate_member_role,
    validate_non_empty_text,
    validate_priority,
)


def _parse_iso_date_or_none(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def _safe_to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


class TimelineWriteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    remark: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def _validate_name(cls, value: Any) -> str | None:
        return validate_non_empty_text(
            value,
            field_name="name",
            empty_message="專案名稱不可為空",
            allow_none=True,
        )

    @field_validator("start_date", mode="before")
    @classmethod
    def _validate_start_date(cls, value: Any) -> str | None:
        return validate_iso_datetime_text(value, field_name="start_date", allow_none=True)

    @field_validator("end_date", mode="before")
    @classmethod
    def _validate_end_date(cls, value: Any) -> str | None:
        return validate_iso_datetime_text(value, field_name="end_date", allow_none=True)


class TimelineCreateRequest(TimelineWriteRequest):
    name: str

    @field_validator("name", mode="before")
    @classmethod
    def _validate_required_name(cls, value: Any) -> str:
        return validate_non_empty_text(
            value,
            field_name="name",
            empty_message="請提供專案名稱（字串）",
            allow_none=False,
        )


class TimelineUpdateRequest(TimelineWriteRequest):
    pass


class TimelineRemarkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    remark: str = ""


class TimelineSearchUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeline_id: int
    email: str


class TimelineAddMemberRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int
    role: int = 1

    @field_validator("role", mode="before")
    @classmethod
    def _validate_role(cls, value: Any) -> int:
        return validate_member_role(value)


class TimelineGenerateTasksRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def _validate_name(cls, value: Any) -> str | None:
        return validate_non_empty_text(
            value,
            field_name="name",
            empty_message="name 不可為空",
            allow_none=True,
        )


class TimelineBatchCreateTasksRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tasks: list[dict]


class TimelineCreateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    remark: str = ""

    @field_validator("name", mode="before")
    @classmethod
    def _validate_name(cls, value: Any) -> str:
        return validate_non_empty_text(
            value,
            field_name="name",
            empty_message="請提供專案名稱（字串）",
            allow_none=False,
        )

    @field_validator("start_date", mode="before")
    @classmethod
    def _validate_start_date(cls, value: Any) -> datetime | None:
        if value in (None, ""):
            return None
        try:
            return datetime.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError("開始日期格式錯誤，請用 YYYY-MM-DD") from exc

    @field_validator("end_date", mode="before")
    @classmethod
    def _validate_end_date(cls, value: Any) -> datetime | None:
        if value in (None, ""):
            return None
        try:
            return datetime.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError("結束日期格式錯誤，請用 YYYY-MM-DD") from exc


class TimelineUpdateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    remark: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def _validate_name(cls, value: Any) -> str | None:
        return validate_non_empty_text(
            value,
            field_name="name",
            empty_message="專案名稱不可為空",
            allow_none=True,
        )

    @field_validator("start_date", mode="before")
    @classmethod
    def _validate_start_date(cls, value: Any) -> datetime | None:
        if value in (None, ""):
            return None
        try:
            return datetime.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError("開始日期格式錯誤") from exc

    @field_validator("end_date", mode="before")
    @classmethod
    def _validate_end_date(cls, value: Any) -> datetime | None:
        if value in (None, ""):
            return None
        try:
            return datetime.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError("結束日期格式錯誤") from exc


class WeeklyReportInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_date_raw: str | None = None
    end_date_raw: str | None = None

    @field_validator("start_date_raw", "end_date_raw")
    @classmethod
    def _validate_date_raw(cls, value, info):
        if value in (None, ""):
            return value
        if not isinstance(value, str):
            raise ValueError(f"{info.field_name} 格式錯誤，請使用 YYYY-MM-DD")
        try:
            datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{info.field_name} 格式錯誤，請使用 YYYY-MM-DD") from exc
        return value


class ConflictCheckInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    end_date: date
    start_date: date | None = None
    assignee_user_id: int | None = None
    task_id: int | None = None
    name: str | None = None
    priority: int = 2
    include_ai_suggestion: bool | None = None

    @field_validator("end_date", mode="before")
    @classmethod
    def _validate_end_date(cls, value):
        parsed = _parse_iso_date_or_none(value)
        if parsed is None:
            raise ValueError("end_date 為必填，格式請使用 YYYY-MM-DD")
        return parsed

    @field_validator("start_date", mode="before")
    @classmethod
    def _validate_start_date(cls, value):
        parsed = _parse_iso_date_or_none(value)
        if value not in (None, "") and parsed is None:
            raise ValueError("start_date 格式錯誤，請使用 YYYY-MM-DD")
        return parsed

    @field_validator("assignee_user_id", "task_id", mode="before")
    @classmethod
    def _normalize_optional_int(cls, value):
        return parse_int_or_none(value)

    @field_validator("name", mode="before")
    @classmethod
    def _normalize_name(cls, value):
        return str(value or "").strip() or None

    @field_validator("priority", mode="before")
    @classmethod
    def _normalize_priority(cls, value):
        parsed = validate_priority(value, allow_none=True)
        if parsed is None:
            return 2
        return parsed

    @field_validator("include_ai_suggestion", mode="before")
    @classmethod
    def _normalize_include_ai_suggestion(cls, value):
        if value is None:
            return None
        return _safe_to_bool(value, default=False)

    @model_validator(mode="after")
    def _fill_and_validate_date_range(self):
        if self.start_date is None:
            self.start_date = self.end_date
        if self.start_date > self.end_date:
            raise ValueError("start_date 不可晚於 end_date")
        return self


class TimelineBatchCreateTasksInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_payloads: list[dict]

    @field_validator("task_payloads")
    @classmethod
    def _validate_task_payloads(cls, value):
        if not isinstance(value, list) or len(value) == 0:
            raise ValueError("請提供至少一個任務")
        return value


class TimelineListItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    startDate: str | None = None
    endDate: str | None = None
    remark: str | None = None
    role: int
    totalTasks: int
    completedTasks: int


class TimelineTaskItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int
    name: str
    assignee: str | None = None
    assistant: list[str] = Field(default_factory=list)
    start_date: str | None = None
    end_date: str | None = None
    completed_at: str | None = None
    completed: bool
    timeline_id: int | None = None
    remark: str | None = None
    isWork: int | bool | None = None
    priority: int
    status: str
    tags: list[str] | str | None = None
    depends_on_task_ids: list[int] = Field(default_factory=list)
    can_manage_members: bool


class TimelineMemberResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int
    name: str
    username: str | None = None
    email: str | None = None
    role: int


class TimelineBatchCreateTasksResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    kept: int
    deleted: int
    created: int
    ignored_dependency_refs: int = 0
    ignored_dependency_ids: int = 0


class UpcomingTimelineResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    end_date: str
    role: int
    is_overdue: bool
    type: str


class TimelineMemberStatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int
    name: str
    role: int
    total_tasks: int
    completed_tasks: int


class TimelineMemberStatsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    members: list[TimelineMemberStatResponse] = Field(default_factory=list)
    status_distribution: dict[str, int]
    total_tasks: int


class TimelineGeneratedTaskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int | None = None
    timeline_id: int | None = None
    status: str | None = None
    completed: bool | None = None
    isExisting: bool
    name: str
    priority: int
    estimated_days: int
    task_remark: str | None = None
    depends_on_task_ids: list[int] = Field(default_factory=list)
    depends_on_task_refs: list[str] = Field(default_factory=list)


class TimelineGenerateTasksResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    tasks: list[TimelineGeneratedTaskResponse] = Field(default_factory=list)
    existingCount: int
    generatedCount: int


class TimelineRiskSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_tasks: int
    projected_duration_days: int
    critical_path_task_count: int
    critical_path_duration_days: int
    risk_item_count: int
    high_risk_count: int
    warning_count: int


class TimelineCriticalPathTaskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int
    name: str
    start_date: str | None = None
    end_date: str | None = None
    duration_days: int
    earliest_start: int
    earliest_finish: int
    latest_start: int
    latest_finish: int
    float_days: int
    is_completed: bool
    depends_on_task_ids: list[int] = Field(default_factory=list)


class TimelineRiskItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int
    name: str
    severity: str
    impact_days: int
    reasons: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    due_date: str | None = None
    depends_on_task_ids: list[int] = Field(default_factory=list)
    float_days: int
    is_critical: bool


class TimelineWarningResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    task_id: int | None = None
    dependency_task_id: int | str | None = None
    source_task_id: int | None = None
    target_task_id: int | None = None
    task_ids: list[int] | None = None


class TimelineRiskGraphNodeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int
    name: str
    status: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    duration_days: int
    float_days: int
    is_critical: bool
    depends_on_task_ids: list[int] = Field(default_factory=list)


class TimelineRiskGraphEdgeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_task_id: int
    target_task_id: int
    is_critical: bool


class TimelineRiskGraphResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[TimelineRiskGraphNodeResponse] = Field(default_factory=list)
    edges: list[TimelineRiskGraphEdgeResponse] = Field(default_factory=list)


class TimelineRiskAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    timeline_id: int
    timeline_name: str
    generated_at: str
    summary: TimelineRiskSummaryResponse
    critical_path: list[TimelineCriticalPathTaskResponse] = Field(default_factory=list)
    risk_items: list[TimelineRiskItemResponse] = Field(default_factory=list)
    warnings: list[TimelineWarningResponse] = Field(default_factory=list)
    graph: TimelineRiskGraphResponse


class TimelineRiskNotificationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    timeline_id: int
    risk_item_count: int
    high_risk_count: int
    warning_count: int
    notified_user_count: int


class WeeklyReportPeriodResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_date: str
    end_date: str


class WeeklyReportOverviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_tasks: int
    completed_tasks: int
    completion_rate: float
    at_risk_tasks: int
    comment_count: int


class WeeklyReportCompletedTaskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int
    name: str
    completed_at: str | None = None
    due_date: str | None = None
    is_late: bool
    owner_name: str | None = None


class WeeklyReportRiskItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int
    name: str
    status: str | None = None
    due_date: str
    reason: str
    days_overdue: int
    days_remaining: int | None = None


class WeeklyReportRecentCommentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comment_id: int
    task_id: int
    task_name: str | None = None
    user_id: int
    message: str
    created_at: str | None = None


class WeeklyReportAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weekly_goal_total: int
    weekly_goal_completed: int
    weekly_goal_completion_rate: float
    previous_completed_tasks: int
    progress_delta: int
    progress_signal: str
    top_owner: str | None = None
    top_tags: list[str] = Field(default_factory=list)
    blocking_comment_count: int
    ai_summary_source: str


class WeeklyReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    timeline_id: int
    timeline_name: str
    period: WeeklyReportPeriodResponse
    overview: WeeklyReportOverviewResponse
    completed_tasks: list[WeeklyReportCompletedTaskResponse] = Field(default_factory=list)
    risk_items: list[WeeklyReportRiskItemResponse] = Field(default_factory=list)
    recent_comments: list[WeeklyReportRecentCommentResponse] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    ai_summary: str
    ai_summary_source: str
    analysis: WeeklyReportAnalysisResponse


class TimelineConflictItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int
    name: str
    status: str | None = None
    start_date: str
    end_date: str
    owner_name: str | None = None
    same_assignee: bool
    reason: str
    timeline_id: int | None = None
    timeline_name: str | None = None
    is_cross_project: bool


class TimelineConflictOverloadDayResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str
    existing_task_count: int
    projected_task_count: int
    threshold: int
    sample_tasks: list[str] = Field(default_factory=list)


class TimelineConflictSuggestionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_date: str
    end_date: str


class TimelineConflictCheckResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    timeline_id: int
    task_name: str | None = None
    priority: int
    priority_label: str
    has_conflict: bool
    conflict_count: int
    assignee_user_id: int
    assignee_name: str | None = None
    is_task_name_redacted: bool
    assignee_conflict_count: int
    project_conflict_count: int
    cross_project_conflict_count: int
    workload_overload_count: int
    workload_overload_days: list[TimelineConflictOverloadDayResponse] = Field(default_factory=list)
    conflicts: list[TimelineConflictItemResponse] = Field(default_factory=list)
    suggestion: TimelineConflictSuggestionResponse | None = None
    ai_suggestion: str = ""
    include_ai_suggestion: bool


class TimelinePlanSuggestedTimelineResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    objective: str


class TimelinePlanSuggestedTaskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    reason: str
    priority: str
    estimated_days: int
    depends_on: list[str] = Field(default_factory=list)


class TimelinePlanSourceReferenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: str
    source_id: str
    title: str
    snippet: str
    score: float


class TimelinePlanMetaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fallback_used: bool
    generated_at: str
    signal_tags: list[str] | None = None
    use_personal_knowledge: bool | None = None
    use_project_knowledge: bool | None = None
    project_id: int | None = None
    retrieved_history_count: int | None = None
    retrieved_knowledge_count: int | None = None


class TimelinePlanSuggestionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    suggested_timeline: TimelinePlanSuggestedTimelineResponse
    suggested_tasks: list[TimelinePlanSuggestedTaskResponse] = Field(default_factory=list)
    source_references: list[TimelinePlanSourceReferenceResponse] = Field(default_factory=list)
    summary: str
    meta: TimelinePlanMetaResponse
