from datetime import datetime, timezone


def utcnow_naive() -> datetime:
    """Return a UTC timestamp stored as naive datetime for current schema compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
