from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


def _to_int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class TaskCreateInput(BaseModel):
    model_config = ConfigDict(extra='ignore')

    status: str = 'pending'
    priority: int = 2
    start_date: datetime | None = None
    end_date: datetime
    timeline_id: int | None = None
    assignee_user_ids: list[int] = []
    depends_on_task_ids: list[int] = []

    @field_validator('status')
    @classmethod
    def _validate_status(cls, value):
        valid = {'pending', 'in_progress', 'review', 'completed', 'cancelled'}
        if value not in valid:
            raise ValueError('status 欄位值不合法')
        return value

    @field_validator('priority', mode='before')
    @classmethod
    def _validate_priority(cls, value):
        parsed = _to_int_or_none(value)
        if parsed is None:
            raise ValueError('priority 必須是數字')
        if parsed < 1 or parsed > 3:
            raise ValueError('priority 必須介於 1 到 3')
        return parsed

    @field_validator('start_date', mode='before')
    @classmethod
    def _validate_start_date(cls, value):
        if value in (None, ''):
            return None
        try:
            return datetime.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError('start_date 格式錯誤') from exc

    @field_validator('end_date', mode='before')
    @classmethod
    def _validate_end_date(cls, value):
        try:
            return datetime.fromisoformat(str(value))
        except (TypeError, ValueError) as exc:
            raise ValueError('end_date 格式錯誤') from exc


class TaskUpdateInput(BaseModel):
    model_config = ConfigDict(extra='ignore')

    name: str | None = None
    timeline_id: int | None = None
    priority: int | None = None
    status: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    depends_on_task_ids: list[int] | None = None

    @field_validator('status')
    @classmethod
    def _validate_status(cls, value):
        if value is None:
            return value
        valid = {'pending', 'in_progress', 'review', 'completed', 'cancelled'}
        if value not in valid:
            raise ValueError('status 欄位值不合法')
        return value

    @field_validator('priority', mode='before')
    @classmethod
    def _validate_priority(cls, value):
        if value is None:
            return value
        parsed = _to_int_or_none(value)
        if parsed is None:
            raise ValueError('priority 必須是數字')
        if parsed < 1 or parsed > 3:
            raise ValueError('priority 必須介於 1 到 3')
        return parsed

    @field_validator('name', mode='before')
    @classmethod
    def _validate_name(cls, value):
        if value is None:
            return value
        if not str(value).strip():
            raise ValueError('name 不可為空')
        return str(value).strip()

    @field_validator('start_date', mode='before')
    @classmethod
    def _validate_start_date(cls, value):
        if value in (None, ''):
            return None
        try:
            return datetime.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError('start_date 格式錯誤') from exc

    @field_validator('end_date', mode='before')
    @classmethod
    def _validate_end_date(cls, value):
        if value in (None, ''):
            return None
        try:
            return datetime.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError('end_date 格式錯誤') from exc


class TaskStatusUpdateInput(BaseModel):
    model_config = ConfigDict(extra='forbid')

    status: str

    @field_validator('status')
    @classmethod
    def _validate_status(cls, value):
        valid_statuses = ['pending', 'in_progress', 'completed']
        if value not in valid_statuses:
            raise ValueError(f'無效的狀態，有效值為: {valid_statuses}')
        return value
