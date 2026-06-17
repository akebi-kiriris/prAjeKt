from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from contracts.shared_fields import validate_non_empty_text


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    username: str | None = None
    email: str
    password: str
    phone: str | None = None

    @field_validator("name", "email", "password", mode="before")
    @classmethod
    def _validate_required_text(cls, value: Any) -> str:
        text = validate_non_empty_text(
            value,
            field_name="field",
            empty_message="欄位不可為空",
            allow_none=False,
        )
        if text is None:
            raise ValueError("欄位不可為空")
        return text

    @field_validator("username", "phone", mode="before")
    @classmethod
    def _validate_optional_text(cls, value: Any) -> str | None:
        return validate_non_empty_text(
            value,
            field_name="field",
            empty_message="欄位不可為空",
            allow_none=True,
        )


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str


class AuthUserResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    username: str | None = None
    email: str


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    username: str | None = None
    email: str
    phone: str | None = None
