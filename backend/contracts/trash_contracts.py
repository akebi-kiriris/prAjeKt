from pydantic import BaseModel, ConfigDict, Field


class TrashTaskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int
    name: str
    deleted_at: str | None = None
    end_date: str | None = None
    priority: int
    is_owner: bool


class TrashTimelineResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    deleted_at: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_owner: bool


class TrashPayloadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tasks: list[TrashTaskResponse] = Field(default_factory=list)
    timelines: list[TrashTimelineResponse] = Field(default_factory=list)
