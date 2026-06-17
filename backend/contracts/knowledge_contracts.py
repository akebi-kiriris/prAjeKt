from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from contracts.shared_fields import normalize_positive_int_list


class KnowledgeDocumentBatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_ids: list[int]

    @field_validator("document_ids", mode="before")
    @classmethod
    def _validate_document_ids(cls, value: Any) -> list[int]:
        return normalize_positive_int_list(
            value,
            field_name="document_ids",
            require_non_empty=False,
        )


class KnowledgeDocumentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    filename: str
    project_id: int | None = None
    mime_type: str | None = None
    file_path: str | None = None
    storage_key: str | None = None
    original_filename: str | None = None
    size_bytes: int | None = None
    has_source_text: bool
    chunk_count: int | None = None
    sha256: str
    status: str
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class KnowledgeMetaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int
    offset: int
    count: int


class KnowledgeDocumentUploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    document: KnowledgeDocumentResponse
    chunk_count: int


class KnowledgeDocumentsListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    documents: list[KnowledgeDocumentResponse] = Field(default_factory=list)
    meta: KnowledgeMetaResponse


class KnowledgeDocumentIdResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    document_id: int


class KnowledgeDocumentReindexResponse(KnowledgeDocumentIdResponse):
    chunk_count: int


class KnowledgeBatchItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: int
    success: bool
    error: str | None = None
    chunk_count: int | None = None


class KnowledgeBatchMetaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    success: int
    failed: int


class KnowledgeBatchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    project_id: int
    results: list[KnowledgeBatchItemResponse] = Field(default_factory=list)
    meta: KnowledgeBatchMetaResponse


class KnowledgeDocumentEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    document_id: int | None = None
    project_id: int
    actor_user_id: int
    event_type: str
    event_payload: dict[str, Any]
    created_at: str | None = None


class KnowledgeDocumentEventsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    events: list[KnowledgeDocumentEventResponse] = Field(default_factory=list)
    meta: KnowledgeMetaResponse
