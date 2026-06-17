from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from contracts.shared_fields import normalize_positive_int, validate_non_empty_text


class GroupCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group_name: str

    @field_validator("group_name", mode="before")
    @classmethod
    def _validate_group_name(cls, value: Any) -> str:
        text = validate_non_empty_text(
            value,
            field_name="group_name",
            empty_message="請輸入群組名稱",
            allow_none=False,
        )
        if text is None:
            raise ValueError("請輸入群組名稱")
        return text


class GroupJoinRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invite_code: str

    @field_validator("invite_code", mode="before")
    @classmethod
    def _validate_invite_code(cls, value: Any) -> str:
        text = validate_non_empty_text(
            value,
            field_name="invite_code",
            empty_message="請輸入邀請碼",
            allow_none=False,
        )
        if text is None:
            raise ValueError("請輸入邀請碼")
        return text


class GroupMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str

    @field_validator("content", mode="before")
    @classmethod
    def _validate_content(cls, value: Any) -> str:
        text = validate_non_empty_text(
            value,
            field_name="content",
            empty_message="content 不可為空",
            allow_none=False,
        )
        if text is None:
            raise ValueError("content 不可為空")
        return text


class GroupSnapshotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    window_days: int | None = None
    async_flag: bool | int | str = Field(default=False, alias="async")

    @field_validator("window_days", mode="before")
    @classmethod
    def _validate_window_days(cls, value: Any) -> int | None:
        if value is None:
            return None
        return normalize_positive_int(value, field_name="window_days")


class GroupListItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group_id: int
    group_name: str
    group_type: str | None = None
    invite_code: str | None = None
    created_at: str | None = None


class GroupMemberResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int
    name: str
    email: str | None = None


class GroupMessageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: int
    content: str
    sender_name: str
    created_at: str | None = None


class GroupRealtimeMessageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: int
    group_id: int
    sender_id: int
    sender_name: str
    content: str
    created_at: str | None = None


class GroupSnapshotResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot_id: int
    group_id: int
    summary: dict[str, Any]
    created_by: int | None = None
    created_at: str | None = None
    source_count: int
    model: str | None = None
    provider: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GroupSnapshotJobResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: str
    group_id: int
    requested_by: int
    window_days: int
    snapshot_id: int | None = None
    snapshot: dict[str, Any] | None = None
    error: str | None = None
    created_at: str
    updated_at: str
