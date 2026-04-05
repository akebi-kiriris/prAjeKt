from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from services.copilot_service import CopilotOperationError, execute_copilot_mcp_request


copilot_bp = Blueprint('copilot', __name__)


def _get_json_dict_or_400():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({'error': '請提供正確的 JSON 物件'}), 400)
    return data, None


def _extract_bearer_token() -> str:
    auth_header = str(request.headers.get('Authorization') or '').strip()
    if not auth_header.lower().startswith('bearer '):
        return ''
    return auth_header.split(' ', 1)[1].strip()


@copilot_bp.route('/mcp/execute', methods=['POST'])
@jwt_required()
def execute_copilot_mcp():
    """Copilot 自然語言入口：由後端選擇 MCP 工具並執行。"""
    data, error = _get_json_dict_or_400()
    if error:
        return error

    message = data.get('message')
    if not isinstance(message, str) or not message.strip():
        return jsonify({'error': '請提供 message（自然語言需求）'}), 400

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
        return jsonify({'error': err.message}), err.status_code
