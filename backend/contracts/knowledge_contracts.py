from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

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
