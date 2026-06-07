from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator
from blueprints.guards import require_timeline_role
from blueprints.validation import format_pydantic_error, validate_payload_or_400
from blueprints.validation import error_from_exception, error_response
from services.timeline_service import (
    TimelineOperationError,
    TimelineAIGenerationError,
    add_timeline_member_for_owner,
    batch_create_tasks_for_timeline,
    build_timeline_member_stats_payload,
    build_timeline_risk_analysis,
    build_weekly_report_for_timeline,
    check_timeline_task_conflicts,
    create_timeline_for_user,
    generate_timeline_tasks_with_ai,
    get_active_timeline_or_404,
    list_timeline_items_for_user,
    list_timeline_members_payload,
    list_timeline_tasks_detail,
    list_upcoming_timelines_for_user,
    remove_timeline_member_for_owner,
    search_timeline_user_by_email,
    soft_delete_timeline_for_owner,
    trigger_timeline_risk_notifications,
    update_timeline_for_member,
    update_timeline_remark_for_member,
)
from services.rag_planning_service import (
    RAGPlanningOperationError,
    suggest_plan_with_rag,
)

timelines_bp = Blueprint('timelines', __name__)

class TimelineCreatePayload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    start_date: str | None = ''
    end_date: str | None = ''
    remark: str | None = ''

    @field_validator('name')
    @classmethod
    def validate_name(cls, value):
        if not str(value).strip():
            raise ValueError('請提供專案名稱（字串）')
        return value

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date(cls, value):
        if value in (None, ''):
            return value
        try:
            datetime.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError('日期格式錯誤') from exc
        return value


class TimelineUpdatePayload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    remark: str | None = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, value):
        if value is None:
            return value
        if not str(value).strip():
            raise ValueError('專案名稱不可為空')
        return value

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date(cls, value):
        if value in (None, ''):
            return value
        try:
            datetime.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError('日期格式錯誤') from exc
        return value


class TimelineConflictPayload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    task_id: int | None = None
    name: str | None = None
    assignee_user_id: int | None = None
    start_date: str
    end_date: str
    priority: int | None = None
    include_ai_suggestion: bool | int | str | None = None


class TimelineRemarkPayload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    remark: str = ''


class TimelineSearchUserPayload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    timeline_id: int
    email: str


class TimelineAddMemberPayload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    user_id: int
    role: int = 1

    @field_validator('role')
    @classmethod
    def validate_role(cls, value):
        if value not in (0, 1):
            raise ValueError('role 只允許 0(負責人) 或 1(協作者)')
        return value


class TimelineGenerateTasksPayload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str | None = None
    description: str | None = None


class TimelineBatchCreateTasksPayload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    tasks: list[dict]


def _pydantic_error_message(err: ValidationError):
    base = format_pydantic_error(
        err,
        integer_field_messages={'role': 'role 必須是數字'},
    )
    if base == '日期格式錯誤':
        first_error = err.errors()[0] if err.errors() else {}
        field = str((first_error.get('loc') or ['欄位'])[-1])
        if field == 'start_date':
            return '開始日期格式錯誤'
        if field == 'end_date':
            return '結束日期格式錯誤'
    return base


def _get_json_dict_or_400():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, error_response("BAD_REQUEST", "請提供正確的 JSON 物件", 400)
    return data, None


def _validate_payload_or_400(model_cls, payload):
    return validate_payload_or_400(
        model_cls,
        payload,
        error_message_builder=_pydantic_error_message,
    )

@timelines_bp.route('', methods=['GET'])
@jwt_required()
def get_timelines():
    """取得使用者的所有專案時程（包含被邀請的）"""
    user_id = int(get_jwt_identity())
    return jsonify(list_timeline_items_for_user(user_id)), 200


@timelines_bp.route('', methods=['POST'])
@jwt_required()
def create_timeline():
    """新增專案時程"""
    user_id = int(get_jwt_identity())
    data, error = _get_json_dict_or_400()
    if error:
        return error
    data, error = _validate_payload_or_400(TimelineCreatePayload, data)
    if error:
        return error
    
    try:
        timeline_id = create_timeline_for_user(user_id, data)
        return jsonify({'message': '專案新增成功', 'id': timeline_id}), 201
    except TimelineOperationError as err:
        return error_from_exception(err)

@timelines_bp.route('/<int:timeline_id>', methods=['PUT'])
@jwt_required()
@require_timeline_role('member')
def update_timeline(timeline_id):
    """更新專案時程（負責人或協作者均可）"""
    data, error = _get_json_dict_or_400()
    if error:
        return error
    data, error = _validate_payload_or_400(TimelineUpdatePayload, data)
    if error:
        return error

    try:
        update_timeline_for_member(timeline_id, int(get_jwt_identity()), data)
        return jsonify({'message': '專案更新成功'}), 200
    except TimelineOperationError as err:
        return error_from_exception(err)

@timelines_bp.route('/<int:timeline_id>', methods=['DELETE'])
@jwt_required()
@require_timeline_role('owner')
def delete_timeline(timeline_id):
    """刪除專案時程（軟刪除，僅負責人可操作）"""
    try:
        soft_delete_timeline_for_owner(timeline_id)
        return jsonify({'message': '專案刪除成功'}), 200
    except TimelineOperationError as err:
        return error_from_exception(err)

@timelines_bp.route('/<int:timeline_id>/tasks', methods=['GET'])
@jwt_required()
@require_timeline_role('member')
def get_timeline_tasks(timeline_id):
    """取得專案的所有任務（含負責人、助理資訊）"""
    user_id = get_jwt_identity()
    return jsonify(list_timeline_tasks_detail(timeline_id, viewer_user_id=user_id)), 200


@timelines_bp.route('/<int:timeline_id>/weekly-report', methods=['GET'])
@jwt_required()
@require_timeline_role('member')
def get_timeline_weekly_report(timeline_id):
    """取得專案週報（完成任務、風險、留言重點與下一步）。"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    try:
        payload = build_weekly_report_for_timeline(timeline_id, start_date, end_date)
        return jsonify(payload), 200
    except TimelineOperationError as err:
        return error_from_exception(err)


@timelines_bp.route('/<int:timeline_id>/risk-analysis', methods=['GET'])
@jwt_required()
@require_timeline_role('member')
def get_timeline_risk_analysis(timeline_id):
    """取得專案關鍵路徑與風險分析"""
    try:
        payload = build_timeline_risk_analysis(timeline_id)
        return jsonify(payload), 200
    except TimelineOperationError as err:
        return error_from_exception(err)


@timelines_bp.route('/<int:timeline_id>/risk-analysis/notify', methods=['POST'])
@jwt_required()
@require_timeline_role('owner')
def notify_timeline_risk_analysis(timeline_id):
    """手動觸發專案風險通知"""
    try:
        payload = trigger_timeline_risk_notifications(timeline_id)
        return jsonify(payload), 200
    except TimelineOperationError as err:
        return error_from_exception(err)


@timelines_bp.route('/<int:timeline_id>/conflict-check', methods=['POST'])
@jwt_required()
@require_timeline_role('member')
def check_timeline_conflict(timeline_id):
    """檢查指定任務時間區間在專案內是否與現有任務衝突。"""
    data, error = _get_json_dict_or_400()
    if error:
        return error
    data, error = _validate_payload_or_400(TimelineConflictPayload, data)
    if error:
        return error

    try:
        payload = check_timeline_task_conflicts(timeline_id, data, int(get_jwt_identity()))
        return jsonify(payload), 200
    except TimelineOperationError as err:
        return error_from_exception(err)


@timelines_bp.route('/ai-suggest-plan', methods=['POST'])
@jwt_required()
def ai_suggest_plan():
    data, error = _get_json_dict_or_400()
    if error:
        return error

    try:
        payload = suggest_plan_with_rag(
            user_id=int(get_jwt_identity()),
            payload=data,
        )
        return jsonify(payload), 200
    except RAGPlanningOperationError as err:
        return error_from_exception(err)


@timelines_bp.route('/<int:timeline_id>/remark', methods=['PUT'])
@jwt_required()
@require_timeline_role('member')
def update_timeline_remark(timeline_id):
    """修改專案備註（負責人或協作者均可）"""
    data, error = _get_json_dict_or_400()
    if error:
        return error
    data, error = _validate_payload_or_400(TimelineRemarkPayload, data)
    if error:
        return error

    try:
        update_timeline_remark_for_member(timeline_id, data.get('remark', ''))
        return jsonify({'message': '備註更新成功'}), 200
    except TimelineOperationError as err:
        return error_from_exception(err)

@timelines_bp.route('/search_user', methods=['POST'])
@jwt_required()
def search_user_by_email():
    """根據 Email 搜尋使用者"""
    data, error = _get_json_dict_or_400()
    if error:
        return error
    data, error = _validate_payload_or_400(TimelineSearchUserPayload, data)
    if error:
        return error

    try:
        user = search_timeline_user_by_email(
            data.get('timeline_id'),
            int(get_jwt_identity()),
            data.get('email'),
        )
        return jsonify({
            'id': user.id,
            'name': user.name,
        }), 200
    except TimelineOperationError as err:
        return error_from_exception(err)

@timelines_bp.route('/<int:timeline_id>/members', methods=['GET'])
@jwt_required()
@require_timeline_role('member')
def get_timeline_members(timeline_id):
    """取得專案成員列表（成員皆可查）"""
    return jsonify(list_timeline_members_payload(timeline_id)), 200


@timelines_bp.route('/<int:timeline_id>/members', methods=['POST'])
@jwt_required()
@require_timeline_role('owner')
def add_timeline_member(timeline_id):
    """邀請人員加入專案（僅負責人可操作）"""
    data, error = _get_json_dict_or_400()
    if error:
        return error
    data, error = _validate_payload_or_400(TimelineAddMemberPayload, data)
    if error:
        return error

    try:
        member_payload = add_timeline_member_for_owner(
            timeline_id=timeline_id,
            invited_user_id=data.get('user_id'),
            role=data.get('role', 1),
            actor_user_id=int(get_jwt_identity()),
        )
        return jsonify(member_payload), 201
    except TimelineOperationError as err:
        return error_from_exception(err)


@timelines_bp.route('/<int:timeline_id>/members/<int:member_user_id>', methods=['DELETE'])
@jwt_required()
@require_timeline_role('owner')
def remove_timeline_member(timeline_id, member_user_id):
    """將成員移出專案（僅負責人可操作，且不能移除自己）"""
    user_id = int(get_jwt_identity())

    try:
        remove_timeline_member_for_owner(timeline_id, member_user_id, user_id)
        return jsonify({'message': '成員已移除'}), 200
    except TimelineOperationError as err:
        return error_from_exception(err)


# ===== AI 任務生成 API =====

@timelines_bp.route('/<int:timeline_id>/generate-tasks', methods=['POST'])
@jwt_required()
@require_timeline_role('member')
def generate_tasks_with_ai(timeline_id):
    """使用 AI 自動生成任務清單（負責人或協作者均可）"""
    data, error = _get_json_dict_or_400()
    if error:
        return error
    data, error = _validate_payload_or_400(TimelineGenerateTasksPayload, data)
    if error:
        return error

    try:
        timeline = get_active_timeline_or_404(timeline_id)
    except TimelineOperationError as err:
        return error_from_exception(err)

    project_name = data.get('name', timeline.name)
    description = data.get('description', timeline.remark or '')
    
    if not project_name.strip():
        return error_response("BAD_REQUEST", "請提供專案名稱", 400)

    try:
        result = generate_timeline_tasks_with_ai(
            timeline_id=timeline_id,
            project_name=project_name,
            description=description,
        )
        return jsonify(result), 200
    except TimelineAIGenerationError as err:
        if err.code == 'missing_api_key':
            return error_response("INTERNAL_ERROR", err.message, 500)
        if err.code == 'json_decode_error':
            return error_response("INTERNAL_ERROR", "AI 回應解析失敗", 500)
        if err.code == 'invalid_payload':
            return error_response("INTERNAL_ERROR", "AI 回傳格式錯誤", 500)
        return error_response("INTERNAL_ERROR", "AI 生成失敗，請稍後再試", 500)


@timelines_bp.route('/<int:timeline_id>/batch-create-tasks', methods=['POST'])
@jwt_required()
@require_timeline_role('member')
def batch_create_tasks(timeline_id):
    """批量創建任務（用於 AI 生成後確認）"""
    user_id = int(get_jwt_identity())
    data, error = _get_json_dict_or_400()
    if error:
        return error
    data, error = _validate_payload_or_400(TimelineBatchCreateTasksPayload, data)
    if error:
        return error

    try:
        payload = batch_create_tasks_for_timeline(timeline_id, user_id, data.get('tasks', []))
        return jsonify(payload), 201
    except TimelineOperationError as err:
        return error_from_exception(err)


@timelines_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_timelines():
    """取得即將到期（3天內）或時間進度超過80%的專案"""
    user_id = int(get_jwt_identity())
    return jsonify(list_upcoming_timelines_for_user(user_id)), 200


@timelines_bp.route('/<int:timeline_id>/member-stats', methods=['GET'])
@jwt_required()
@require_timeline_role('owner')
def get_member_stats(timeline_id):
    """取得專案成員任務統計（負責人限定）"""
    return jsonify(build_timeline_member_stats_payload(timeline_id)), 200
