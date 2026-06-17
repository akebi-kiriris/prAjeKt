from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    type: str
    title: str
    content: str | None = None
    link: str | None = None
    is_read: bool
    created_at: str | None = None
