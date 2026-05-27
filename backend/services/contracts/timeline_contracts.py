from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


def _parse_iso_date_or_none(value: Any) -> date | None:
    if value in (None, ''):
        return None
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def _safe_to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
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
        if normalized in {'1', 'true', 'yes', 'on'}:
            return True
        if normalized in {'0', 'false', 'no', 'off'}:
            return False
    return default


class WeeklyReportInput(BaseModel):
    model_config = ConfigDict(extra='forbid')

    start_date_raw: str | None = None
    end_date_raw: str | None = None

    @field_validator('start_date_raw', 'end_date_raw')
    @classmethod
    def _validate_date_raw(cls, value, info):
        if value in (None, ''):
            return value
        if not isinstance(value, str):
            raise ValueError(f'{info.field_name} 格式錯誤，請使用 YYYY-MM-DD')
        try:
            datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f'{info.field_name} 格式錯誤，請使用 YYYY-MM-DD') from exc
        return value


class ConflictCheckInput(BaseModel):
    model_config = ConfigDict(extra='forbid')

    end_date: date
    start_date: date | None = None
    assignee_user_id: int | None = None
    task_id: int | None = None
    name: str | None = None
    priority: int = 2
    include_ai_suggestion: bool | None = None

    @field_validator('end_date', mode='before')
    @classmethod
    def _validate_end_date(cls, value):
        parsed = _parse_iso_date_or_none(value)
        if parsed is None:
            raise ValueError('end_date 為必填，格式請使用 YYYY-MM-DD')
        return parsed

    @field_validator('start_date', mode='before')
    @classmethod
    def _validate_start_date(cls, value):
        parsed = _parse_iso_date_or_none(value)
        if value not in (None, '') and parsed is None:
            raise ValueError('start_date 格式錯誤，請使用 YYYY-MM-DD')
        return parsed

    @field_validator('assignee_user_id', 'task_id', mode='before')
    @classmethod
    def _normalize_optional_int(cls, value):
        return _safe_to_int(value)

    @field_validator('name', mode='before')
    @classmethod
    def _normalize_name(cls, value):
        return str(value or '').strip() or None

    @field_validator('priority', mode='before')
    @classmethod
    def _normalize_priority(cls, value):
        parsed = _safe_to_int(value)
        if parsed in (1, 2, 3):
            return parsed
        return 2

    @field_validator('include_ai_suggestion', mode='before')
    @classmethod
    def _normalize_include_ai_suggestion(cls, value):
        if value is None:
            return None
        return _safe_to_bool(value, default=False)

    @model_validator(mode='after')
    def _fill_and_validate_date_range(self):
        if self.start_date is None:
            self.start_date = self.end_date
        if self.start_date > self.end_date:
            raise ValueError('start_date 不可晚於 end_date')
        return self


class TimelineBatchCreateTasksInput(BaseModel):
    model_config = ConfigDict(extra='forbid')

    task_payloads: list[dict]

    @field_validator('task_payloads')
    @classmethod
    def _validate_task_payloads(cls, value):
        if not isinstance(value, list) or len(value) == 0:
            raise ValueError('請提供至少一個任務')
        return value
