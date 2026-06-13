from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from blueprints.validation import error_from_exception, error_response
from services.agent_trace_service import build_agent_request_id
from services.copilot_service import (
    CopilotOperationError,
    create_copilot_agent_plan,
    execute_copilot_agent_plan,
    execute_copilot_mcp_request,
    reject_copilot_agent_plan,
)
from services.tools.registry import list_registered_tools


copilot_bp = Blueprint('copilot', __name__)


def _get_json_dict_or_400():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, error_response("BAD_REQUEST", "請提供正確的 JSON 物件", 400)
    return data, None


def _extract_bearer_token() -> str:
    auth_header = str(request.headers.get('Authorization') or '').strip()
    if not auth_header.lower().startswith('bearer '):
        return ''
    return auth_header.split(' ', 1)[1].strip()


def _resolve_request_id(data: dict | None = None) -> str:
    header_request_id = str(request.headers.get('X-Request-Id') or '').strip()
    if header_request_id:
        return header_request_id
    if isinstance(data, dict):
        body_request_id = data.get('request_id')
        if isinstance(body_request_id, str) and body_request_id.strip():
            return body_request_id.strip()
    return build_agent_request_id()


@copilot_bp.route('/mcp/execute', methods=['POST'])
@jwt_required()
def execute_copilot_mcp():
    """Copilot 自然語言入口：由後端選擇 MCP 工具並執行。"""
    data, error = _get_json_dict_or_400()
    if error:
        return error

    message = data.get('message')
    if not isinstance(message, str) or not message.strip():
        return error_response("BAD_REQUEST", "請提供 message（自然語言需求）", 400)

    context = data.get('context') if isinstance(data.get('context'), dict) else {}
    preferred_tool = data.get('preferred_tool') if isinstance(data.get('preferred_tool'), str) else None
    tool_arguments = data.get('tool_arguments') if isinstance(data.get('tool_arguments'), dict) else {}
    auto_create_generated_tasks = bool(data.get('auto_create_generated_tasks', False))

    try:
        payload = execute_copilot_mcp_request(
            user_message=message,
            context=context,
            preferred_tool=preferred_tool,
            tool_arguments=tool_arguments,
            auto_create_generated_tasks=auto_create_generated_tasks,
            access_token=_extract_bearer_token(),
        )
        return jsonify(payload), 200
    except CopilotOperationError as err:
        return error_from_exception(err)


@copilot_bp.route('/agent/tools', methods=['GET'])
@jwt_required()
def list_copilot_agent_tools():
    """回傳單體 registry 已開放給 agent 的工具清單。"""
    return jsonify({"tools": list_registered_tools()}), 200


@copilot_bp.route('/agent/execute', methods=['POST'])
@jwt_required()
def execute_copilot_agent():
    """Copilot Agent 執行入口（僅執行已確認計畫）。"""
    data, error = _get_json_dict_or_400()
    if error:
        return error

    user_id = int(get_jwt_identity())
    tool_payloads = data.get('tool_payloads') if isinstance(data.get('tool_payloads'), dict) else {}
    max_loops = data.get('max_loops', 6)
    try:
        max_loops = int(max_loops)
    except (TypeError, ValueError):
        return error_response("BAD_REQUEST", "max_loops 必須為整數", 400)
    if max_loops <= 0:
        return error_response("BAD_REQUEST", "max_loops 必須大於 0", 400)

    plan_id = data.get('plan_id')
    if not isinstance(plan_id, str) or not plan_id.strip():
        return error_response("BAD_REQUEST", "execute 階段必須提供 plan_id。", 400)

    confirm = data.get('confirm')
    if not isinstance(confirm, bool):
        return error_response("BAD_REQUEST", "confirm 必須為布林值 true/false。", 400)
    request_id = _resolve_request_id(data)

    try:
        payload = execute_copilot_agent_plan(
            plan_id=plan_id,
            user_id=user_id,
            confirm=confirm,
            tool_payloads=tool_payloads,
            max_loops=max_loops,
            request_id=request_id,
        )
        return jsonify(payload), 200
    except CopilotOperationError as err:
        return error_from_exception(err)


@copilot_bp.route('/agent/plan', methods=['POST'])
@jwt_required()
def create_agent_plan():
    """建立 agent 計畫（只規劃，不執行）。"""
    data, error = _get_json_dict_or_400()
    if error:
        return error

    message = data.get('message')
    if not isinstance(message, str) or not message.strip():
        return error_response("BAD_REQUEST", "請提供 message（自然語言需求）", 400)

    context = data.get('context') if isinstance(data.get('context'), dict) else {}
    context['user_id'] = int(get_jwt_identity())
    tool_payloads = data.get('tool_payloads') if isinstance(data.get('tool_payloads'), dict) else {}
    request_id = _resolve_request_id(data)
    try:
        payload = create_copilot_agent_plan(
            user_message=message,
            user_id=int(get_jwt_identity()),
            context=context,
            tool_payloads=tool_payloads,
            request_id=request_id,
        )
        return jsonify(payload), 200
    except CopilotOperationError as err:
        return error_from_exception(err)


@copilot_bp.route('/agent/reject', methods=['POST'])
@jwt_required()
def reject_agent_plan():
    """拒絕既有 agent 計畫。"""
    data, error = _get_json_dict_or_400()
    if error:
        return error

    plan_id = data.get('plan_id')
    if not isinstance(plan_id, str) or not plan_id.strip():
        return error_response("BAD_REQUEST", "請提供 plan_id", 400)

    reason = data.get('reason') if isinstance(data.get('reason'), str) else None
    request_id = _resolve_request_id(data)
    try:
        payload = reject_copilot_agent_plan(
            plan_id=plan_id,
            user_id=int(get_jwt_identity()),
            reason=reason,
            request_id=request_id,
        )
        return jsonify(payload), 200
    except CopilotOperationError as err:
        return error_from_exception(err)


@copilot_bp.route('/agent/replan', methods=['POST'])
@jwt_required()
def replan_agent():
    """重新規劃（可選擇帶原 plan_id 先標記拒絕）。"""
    data, error = _get_json_dict_or_400()
    if error:
        return error

    message = data.get('message')
    if not isinstance(message, str) or not message.strip():
        return error_response("BAD_REQUEST", "請提供 message（自然語言需求）", 400)

    old_plan_id = data.get('plan_id')
    user_id = int(get_jwt_identity())
    request_id = _resolve_request_id(data)
    if isinstance(old_plan_id, str) and old_plan_id.strip():
        try:
            reject_copilot_agent_plan(
                plan_id=old_plan_id,
                user_id=user_id,
                reason='replan',
                request_id=request_id,
            )
        except CopilotOperationError:
            pass

    context = data.get('context') if isinstance(data.get('context'), dict) else {}
    context['user_id'] = user_id
    tool_payloads = data.get('tool_payloads') if isinstance(data.get('tool_payloads'), dict) else {}
    try:
        payload = create_copilot_agent_plan(
            user_message=message,
            user_id=user_id,
            context=context,
            tool_payloads=tool_payloads,
            force_model_proposal=True,
            request_id=request_id,
        )
        return jsonify(payload), 200
    except CopilotOperationError as err:
        return error_from_exception(err)
