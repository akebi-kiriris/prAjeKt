from pathlib import Path

import pytest
from pydantic import ValidationError

from contracts.response_contracts import (
    CompletionResponse,
    MessageResponse,
    TaskIdMutationResponse,
    response_payload,
)
from openapi_document import build_openapi_document, export_openapi_document


def test_response_payload_preserves_existing_mutation_shape():
    payload = response_payload(TaskIdMutationResponse(message="任務新增成功", task_id=123))

    assert payload == {
        "message": "任務新增成功",
        "task_id": 123,
    }


def test_response_contract_forbids_unexpected_fields():
    with pytest.raises(ValidationError):
        MessageResponse(message="ok", unexpected=True)


def test_completion_response_shape_matches_frontend_contract():
    payload = response_payload(CompletionResponse(message="狀態更新成功", completed=True))

    assert payload == {
        "message": "狀態更新成功",
        "completed": True,
    }


def test_openapi_document_lists_primary_contract_entrypoints():
    document = build_openapi_document()

    assert document["openapi"] == "3.1.0"
    assert document["info"]["title"] == "Learnlink Backend API"
    assert "/tasks" in document["paths"]
    assert "/tasks/{task_id}/files/{file_id}" in document["paths"]
    assert "/timelines/{timeline_id}/weekly-report" in document["paths"]
    assert "/knowledge/documents" in document["paths"]
    assert "/copilot/agent/tools" in document["paths"]


def test_openapi_document_includes_request_response_schemas():
    document = build_openapi_document()

    task_create_schema = document["paths"]["/tasks"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    weekly_report_response = document["paths"]["/timelines/{timeline_id}/weekly-report"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]

    assert task_create_schema["$ref"] == "#/components/schemas/TaskCreateRequest"
    assert weekly_report_response["$ref"] == "#/components/schemas/WeeklyReportResponse"
    assert "TaskCreateRequest" in document["components"]["schemas"]
    assert "WeeklyReportResponse" in document["components"]["schemas"]
    assert "bearerAuth" in document["components"]["securitySchemes"]


def test_export_openapi_document_writes_json_file():
    output_path = Path("instance/test_openapi_export.json")

    try:
        destination = export_openapi_document(output_path)

        assert destination == output_path
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert '"openapi": "3.1.0"' in content
    finally:
        if output_path.exists():
            output_path.unlink()
