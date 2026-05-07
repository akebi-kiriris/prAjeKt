from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

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


@knowledge_bp.route("/documents", methods=["POST"])
@jwt_required()
def upload_knowledge_document_api():
    if "file" not in request.files:
        return jsonify({"error": "沒有選擇檔案"}), 400

    user_id = int(get_jwt_identity())
    file_storage = request.files["file"]
    project_id = request.args.get("project_id")
    if project_id is not None:
        try:
            project_id = int(project_id)
        except ValueError:
            return jsonify({"error": "project_id 必須為數字"}), 400
        # 檢查使用者是否為該專案 (timeline) 成員
        member = get_timeline_member(project_id, user_id)
        if member is None:
            return jsonify({"error": "沒有權限上傳至該專案檔案區"}), 403
    try:
        payload = upload_and_index_knowledge_document(user_id=user_id, file_storage=file_storage, project_id=project_id)
        return jsonify(payload), 201
    except KnowledgeOperationError as err:
        return jsonify({"error": err.message}), err.status_code


@knowledge_bp.route("/documents", methods=["GET"])
@jwt_required()
def list_knowledge_documents_api():
    user_id = int(get_jwt_identity())
    try:
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return jsonify({"error": "limit 與 offset 必須為數字"}), 400

    project_id = request.args.get("project_id")
    if project_id is not None:
        try:
            project_id = int(project_id)
        except ValueError:
            return jsonify({"error": "project_id 必須為數字"}), 400
        member = get_timeline_member(project_id, user_id)
        if member is None:
            return jsonify({"error": "沒有權限查看該專案檔案區"}), 403

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
        return jsonify({"error": err.message}), err.status_code


@knowledge_bp.route("/documents/<int:document_id>", methods=["DELETE"])
@jwt_required()
def delete_knowledge_document_api(document_id):
    user_id = int(get_jwt_identity())
    project_id = request.args.get("project_id")
    if project_id is not None:
        try:
            project_id = int(project_id)
        except ValueError:
            return jsonify({"error": "project_id 必須為數字"}), 400
        member = get_timeline_member(project_id, user_id)
        if member is None:
            return jsonify({"error": "沒有權限刪除該專案檔案"}), 403
    try:
        payload = delete_knowledge_document(user_id=user_id, document_id=document_id, project_id=project_id)
        return jsonify(payload), 200
    except KnowledgeOperationError as err:
        return jsonify({"error": err.message}), err.status_code


@knowledge_bp.route("/documents/<int:document_id>/reindex", methods=["POST"])
@jwt_required()
def reindex_knowledge_document_api(document_id):
    user_id = int(get_jwt_identity())
    project_id = request.args.get("project_id")
    if project_id is not None:
        try:
            project_id = int(project_id)
        except ValueError:
            return jsonify({"error": "project_id 必須為數字"}), 400
        member = get_timeline_member(project_id, user_id)
        if member is None:
            return jsonify({"error": "沒有權限重建該專案檔案索引"}), 403
    try:
        payload = reindex_knowledge_document(user_id=user_id, document_id=document_id, project_id=project_id)
        return jsonify(payload), 200
    except KnowledgeOperationError as err:
        return jsonify({"error": err.message}), err.status_code


def _require_project_membership(user_id):
    project_id = request.args.get("project_id")
    if project_id is None:
        return None, (jsonify({"error": "project_id 為必填"}), 400)
    try:
        project_id = int(project_id)
    except ValueError:
        return None, (jsonify({"error": "project_id 必須為數字"}), 400)
    member = get_timeline_member(project_id, user_id)
    if member is None:
        return None, (jsonify({"error": "沒有權限操作該專案檔案區"}), 403)
    return project_id, None


@knowledge_bp.route("/documents/batch-delete", methods=["POST"])
@jwt_required()
def batch_delete_knowledge_documents_api():
    user_id = int(get_jwt_identity())
    project_id, error_response = _require_project_membership(user_id)
    if error_response:
        return error_response
    payload = request.get_json(silent=True) or {}
    document_ids = payload.get("document_ids")
    if not isinstance(document_ids, list) or len(document_ids) == 0:
        return jsonify({"error": "document_ids 必須為非空陣列"}), 400
    try:
        result = batch_delete_knowledge_documents(user_id=user_id, project_id=project_id, document_ids=document_ids)
        return jsonify(result), 200
    except KnowledgeOperationError as err:
        return jsonify({"error": err.message}), err.status_code


@knowledge_bp.route("/documents/batch-reindex", methods=["POST"])
@jwt_required()
def batch_reindex_knowledge_documents_api():
    user_id = int(get_jwt_identity())
    project_id, error_response = _require_project_membership(user_id)
    if error_response:
        return error_response
    payload = request.get_json(silent=True) or {}
    document_ids = payload.get("document_ids")
    if not isinstance(document_ids, list) or len(document_ids) == 0:
        return jsonify({"error": "document_ids 必須為非空陣列"}), 400
    try:
        result = batch_reindex_knowledge_documents(user_id=user_id, project_id=project_id, document_ids=document_ids)
        return jsonify(result), 200
    except KnowledgeOperationError as err:
        return jsonify({"error": err.message}), err.status_code


@knowledge_bp.route("/documents/<int:document_id>/download", methods=["GET"])
@jwt_required()
def download_knowledge_document_api(document_id):
    user_id = int(get_jwt_identity())
    project_id, error_response = _require_project_membership(user_id)
    if error_response:
        return error_response
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
        return jsonify({"error": err.message}), err.status_code


@knowledge_bp.route("/documents/<int:document_id>/preview", methods=["GET"])
@jwt_required()
def preview_knowledge_document_api(document_id):
    user_id = int(get_jwt_identity())
    project_id, error_response = _require_project_membership(user_id)
    if error_response:
        return error_response
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
        return jsonify({"error": err.message}), err.status_code


@knowledge_bp.route("/documents/events", methods=["GET"])
@jwt_required()
def list_knowledge_document_events_api():
    user_id = int(get_jwt_identity())
    project_id, error_response = _require_project_membership(user_id)
    if error_response:
        return error_response
    try:
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return jsonify({"error": "limit 與 offset 必須為數字"}), 400
    payload = list_project_knowledge_events(project_id=project_id, limit=limit, offset=offset)
    return jsonify(payload), 200
