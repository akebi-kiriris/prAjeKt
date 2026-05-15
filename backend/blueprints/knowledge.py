from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from pydantic import BaseModel, ConfigDict
from blueprints.validation import error_from_exception, error_response, validate_payload_or_400

from services.knowledge_service import (
    KnowledgeOperationError,
    batch_delete_knowledge_documents,
    batch_reindex_knowledge_documents,
    delete_knowledge_document,
    get_project_knowledge_document_file,
    list_knowledge_documents,
    list_project_knowledge_events,
    reindex_knowledge_document,
    upload_and_index_knowledge_document,
)
from repositories.timeline_repository import get_timeline_member


knowledge_bp = Blueprint("knowledge", __name__)


class KnowledgeBatchPayload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    document_ids: list[int]


def _validate_payload_or_400(model_cls, payload):
    return validate_payload_or_400(model_cls, payload)


def _parse_int_query_arg_or_400(name, default=None):
    raw = request.args.get(name, default)
    try:
        return int(raw), None
    except (TypeError, ValueError):
        return None, error_response("BAD_REQUEST", f"{name} 必須為數字", 400)


def _parse_optional_project_id():
    project_id = request.args.get("project_id")
    if project_id is None:
        return None, None
    try:
        return int(project_id), None
    except ValueError:
        return None, error_response("BAD_REQUEST", "project_id 必須為數字", 400)


@knowledge_bp.route("/documents", methods=["POST"])
@jwt_required()
def upload_knowledge_document_api():
    if "file" not in request.files:
        return error_response("BAD_REQUEST", "沒有選擇檔案", 400)

    user_id = int(get_jwt_identity())
    file_storage = request.files["file"]
    project_id, error = _parse_optional_project_id()
    if error:
        return error
    if project_id is not None:
        # 檢查使用者是否為該專案 (timeline) 成員
        member = get_timeline_member(project_id, user_id)
        if member is None:
            return error_response("FORBIDDEN", "沒有權限上傳至該專案檔案區", 403)
    try:
        payload = upload_and_index_knowledge_document(user_id=user_id, file_storage=file_storage, project_id=project_id)
        return jsonify(payload), 201
    except KnowledgeOperationError as err:
        return error_from_exception(err)


@knowledge_bp.route("/documents", methods=["GET"])
@jwt_required()
def list_knowledge_documents_api():
    user_id = int(get_jwt_identity())
    limit, limit_error = _parse_int_query_arg_or_400("limit", 50)
    if limit_error:
        return limit_error
    offset, offset_error = _parse_int_query_arg_or_400("offset", 0)
    if offset_error:
        return offset_error

    project_id, project_error = _parse_optional_project_id()
    if project_error:
        return project_error
    if project_id is not None:
        member = get_timeline_member(project_id, user_id)
        if member is None:
            return error_response("FORBIDDEN", "沒有權限查看該專案檔案區", 403)

    try:
        q = (request.args.get("q") or "").strip() or None
        sort = (request.args.get("sort") or "created_desc").strip().lower()
        status = (request.args.get("status") or "").strip() or None
        payload = list_knowledge_documents(
            user_id=user_id,
            limit=limit,
            offset=offset,
            project_id=project_id,
            q=q,
            sort=sort,
            status=status,
        )
        return jsonify(payload), 200
    except KnowledgeOperationError as err:
        return error_from_exception(err)


@knowledge_bp.route("/documents/<int:document_id>", methods=["DELETE"])
@jwt_required()
def delete_knowledge_document_api(document_id):
    user_id = int(get_jwt_identity())
    project_id, error = _parse_optional_project_id()
    if error:
        return error
    if project_id is not None:
        member = get_timeline_member(project_id, user_id)
        if member is None:
            return error_response("FORBIDDEN", "沒有權限刪除該專案檔案", 403)
    try:
        payload = delete_knowledge_document(user_id=user_id, document_id=document_id, project_id=project_id)
        return jsonify(payload), 200
    except KnowledgeOperationError as err:
        return error_from_exception(err)


@knowledge_bp.route("/documents/<int:document_id>/reindex", methods=["POST"])
@jwt_required()
def reindex_knowledge_document_api(document_id):
    user_id = int(get_jwt_identity())
    project_id, error = _parse_optional_project_id()
    if error:
        return error
    if project_id is not None:
        member = get_timeline_member(project_id, user_id)
        if member is None:
            return error_response("FORBIDDEN", "沒有權限重建該專案檔案索引", 403)
    try:
        payload = reindex_knowledge_document(user_id=user_id, document_id=document_id, project_id=project_id)
        return jsonify(payload), 200
    except KnowledgeOperationError as err:
        return error_from_exception(err)


def _require_project_membership(user_id):
    project_id = request.args.get("project_id")
    if project_id is None:
        return None, error_response("BAD_REQUEST", "project_id 為必填", 400)
    try:
        project_id = int(project_id)
    except ValueError:
        return None, error_response("BAD_REQUEST", "project_id 必須為數字", 400)
    member = get_timeline_member(project_id, user_id)
    if member is None:
        return None, error_response("FORBIDDEN", "沒有權限操作該專案檔案區", 403)
    return project_id, None


@knowledge_bp.route("/documents/batch-delete", methods=["POST"])
@jwt_required()
def batch_delete_knowledge_documents_api():
    user_id = int(get_jwt_identity())
    project_id, membership_error = _require_project_membership(user_id)
    if membership_error:
        return membership_error
    payload = request.get_json(silent=True) or {}
    payload, payload_error = _validate_payload_or_400(KnowledgeBatchPayload, payload)
    if payload_error:
        return payload_error
    document_ids = payload["document_ids"]
    if len(document_ids) == 0:
        return error_response("BAD_REQUEST", "document_ids 必須為非空陣列", 400)
    try:
        result = batch_delete_knowledge_documents(user_id=user_id, project_id=project_id, document_ids=document_ids)
        return jsonify(result), 200
    except KnowledgeOperationError as err:
        return error_from_exception(err)


@knowledge_bp.route("/documents/batch-reindex", methods=["POST"])
@jwt_required()
def batch_reindex_knowledge_documents_api():
    user_id = int(get_jwt_identity())
    project_id, membership_error = _require_project_membership(user_id)
    if membership_error:
        return membership_error
    payload = request.get_json(silent=True) or {}
    payload, payload_error = _validate_payload_or_400(KnowledgeBatchPayload, payload)
    if payload_error:
        return payload_error
    document_ids = payload["document_ids"]
    if len(document_ids) == 0:
        return error_response("BAD_REQUEST", "document_ids 必須為非空陣列", 400)
    try:
        result = batch_reindex_knowledge_documents(user_id=user_id, project_id=project_id, document_ids=document_ids)
        return jsonify(result), 200
    except KnowledgeOperationError as err:
        return error_from_exception(err)


@knowledge_bp.route("/documents/<int:document_id>/download", methods=["GET"])
@jwt_required()
def download_knowledge_document_api(document_id):
    user_id = int(get_jwt_identity())
    project_id, membership_error = _require_project_membership(user_id)
    if membership_error:
        return membership_error
    try:
        document = get_project_knowledge_document_file(
            user_id=user_id,
            project_id=project_id,
            document_id=document_id,
            event_type="download",
        )
        return send_file(
            document.file_path,
            as_attachment=True,
            download_name=document.original_filename or document.filename,
            mimetype=document.mime_type or "application/octet-stream",
        )
    except KnowledgeOperationError as err:
        return error_from_exception(err)


@knowledge_bp.route("/documents/<int:document_id>/preview", methods=["GET"])
@jwt_required()
def preview_knowledge_document_api(document_id):
    user_id = int(get_jwt_identity())
    project_id, membership_error = _require_project_membership(user_id)
    if membership_error:
        return membership_error
    try:
        document = get_project_knowledge_document_file(
            user_id=user_id,
            project_id=project_id,
            document_id=document_id,
            event_type="preview",
        )
        mime = (document.mime_type or "").lower()
        inline_mime = mime or "application/octet-stream"
        return send_file(
            document.file_path,
            as_attachment=False,
            download_name=document.original_filename or document.filename,
            mimetype=inline_mime,
        )
    except KnowledgeOperationError as err:
        return error_from_exception(err)


@knowledge_bp.route("/documents/events", methods=["GET"])
@jwt_required()
def list_knowledge_document_events_api():
    user_id = int(get_jwt_identity())
    project_id, membership_error = _require_project_membership(user_id)
    if membership_error:
        return membership_error
    limit, limit_error = _parse_int_query_arg_or_400("limit", 50)
    if limit_error:
        return limit_error
    offset, offset_error = _parse_int_query_arg_or_400("offset", 0)
    if offset_error:
        return offset_error
    payload = list_project_knowledge_events(project_id=project_id, limit=limit, offset=offset)
    return jsonify(payload), 200
