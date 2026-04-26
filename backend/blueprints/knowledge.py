from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from services.knowledge_service import (
    KnowledgeOperationError,
    delete_knowledge_document,
    list_knowledge_documents,
    reindex_knowledge_document,
    upload_and_index_knowledge_document,
)


knowledge_bp = Blueprint("knowledge", __name__)


@knowledge_bp.route("/documents", methods=["POST"])
@jwt_required()
def upload_knowledge_document_api():
    if "file" not in request.files:
        return jsonify({"error": "沒有選擇檔案"}), 400

    user_id = int(get_jwt_identity())
    file_storage = request.files["file"]
    try:
        payload = upload_and_index_knowledge_document(user_id=user_id, file_storage=file_storage)
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

    try:
        payload = list_knowledge_documents(user_id=user_id, limit=limit, offset=offset)
        return jsonify(payload), 200
    except KnowledgeOperationError as err:
        return jsonify({"error": err.message}), err.status_code


@knowledge_bp.route("/documents/<int:document_id>", methods=["DELETE"])
@jwt_required()
def delete_knowledge_document_api(document_id):
    user_id = int(get_jwt_identity())
    try:
        payload = delete_knowledge_document(user_id=user_id, document_id=document_id)
        return jsonify(payload), 200
    except KnowledgeOperationError as err:
        return jsonify({"error": err.message}), err.status_code


@knowledge_bp.route("/documents/<int:document_id>/reindex", methods=["POST"])
@jwt_required()
def reindex_knowledge_document_api(document_id):
    user_id = int(get_jwt_identity())
    try:
        payload = reindex_knowledge_document(user_id=user_id, document_id=document_id)
        return jsonify(payload), 200
    except KnowledgeOperationError as err:
        return jsonify({"error": err.message}), err.status_code
