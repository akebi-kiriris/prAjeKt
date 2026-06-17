from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from contracts.shared_fields import validate_non_empty_text


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    username: str | None = None
    email: str | None = None
    bio: str | None = None
    avatar: str | None = None
    phone: str | None = None
    current_password: str | None = None
    new_password: str | None = None

    @field_validator("name", "username", "email", "current_password", "new_password", mode="before")
    @classmethod
    def _validate_optional_non_empty_text(cls, value: Any) -> str | None:
        return validate_non_empty_text(
            value,
            field_name="field",
            empty_message="欄位不可為空",
            allow_none=True,
        )


class ProfileSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str

    @field_validator("query", mode="before")
    @classmethod
    def _validate_query(cls, value: Any) -> str:
        text = validate_non_empty_text(
            value,
            field_name="query",
            empty_message="請提供查詢關鍵字",
            allow_none=False,
        )
        if text is None:
            raise ValueError("請提供查詢關鍵字")
        return text


class ProfileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    username: str | None = None
    email: str
    phone: str | None = None
    avatar: str | None = None
    bio: str | None = None
    created_at: str | None = None


class ProfileSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    username: str | None = None
    email: str


class DailyCompletionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str
    count: int


class TasksByProjectResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    count: int


class ProfileChartStatsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status_distribution: dict[str, int]
    daily_completions: list[DailyCompletionResponse] = Field(default_factory=list)
    tasks_by_project: list[TasksByProjectResponse] = Field(default_factory=list)
