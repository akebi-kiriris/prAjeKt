from datetime import datetime
from typing import Any


TASK_STATUS_VALUES = {"pending", "in_progress", "review", "completed", "cancelled"}
TASK_STATUS_BOARD_VALUES = {"pending", "in_progress", "completed"}
MEMBER_ROLE_VALUES = {0, 1}


def parse_int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def validate_non_empty_text(
    value: Any,
    *,
    field_name: str,
    empty_message: str,
    allow_none: bool = False,
) -> str | None:
    if value is None:
        if allow_none:
            return None
        raise ValueError(empty_message)
    text = str(value).strip()
    if not text:
        raise ValueError(empty_message)
    return text


def validate_iso_datetime_text(
    value: Any,
    *,
    field_name: str,
    allow_none: bool = True,
) -> str | None:
    if value in (None, ""):
        if allow_none:
            return None
        raise ValueError(f"{field_name} 格式錯誤")
    try:
        datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"{field_name} 格式錯誤") from exc
    return str(value)


def parse_iso_datetime_or_none(value: Any, *, field_name: str) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"{field_name} 格式錯誤") from exc


def validate_priority(
    value: Any,
    *,
    allow_none: bool = True,
) -> int | None:
    if value is None:
        if allow_none:
            return None
        raise ValueError("priority 必須是數字")
    parsed = parse_int_or_none(value)
    if parsed is None:
        raise ValueError("priority 必須是數字")
    if parsed < 1 or parsed > 3:
        raise ValueError("priority 必須介於 1 到 3")
    return parsed


def validate_task_status(value: Any, *, allow_none: bool = True) -> str | None:
    if value is None:
        if allow_none:
            return None
        raise ValueError("status 欄位值不合法")
    if value not in TASK_STATUS_VALUES:
        raise ValueError("status 欄位值不合法")
    return str(value)


def validate_member_role(value: Any) -> int:
    parsed = parse_int_or_none(value)
    if parsed not in MEMBER_ROLE_VALUES:
        raise ValueError("role 只允許 0(負責人) 或 1(協作者)")
    return parsed


def normalize_optional_int(value: Any, *, field_name: str) -> int | None:
    if value in (None, ""):
        return None
    parsed = parse_int_or_none(value)
    if parsed is None:
        raise ValueError(f"{field_name} 必須是整數")
    return parsed


def normalize_positive_int(value: Any, *, field_name: str) -> int:
    parsed = parse_int_or_none(value)
    if parsed is None or parsed <= 0:
        raise ValueError(f"{field_name} 必須是正整數")
    return parsed


def normalize_positive_int_list(
    value: Any,
    *,
    field_name: str,
    require_non_empty: bool = False,
) -> list[int]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} 必須是陣列")
    normalized: list[int] = []
    seen: set[int] = set()
    for item in value:
        parsed = parse_int_or_none(item)
        if parsed is None or parsed <= 0:
            raise ValueError(f"{field_name} 只允許正整數 ID")
        if parsed in seen:
            continue
        seen.add(parsed)
        normalized.append(parsed)
    if require_non_empty and len(normalized) == 0:
        raise ValueError(f"{field_name} 必須為非空陣列")
    return normalized
