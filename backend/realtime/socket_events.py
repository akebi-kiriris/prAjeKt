from flask import request
from flask_socketio import emit, join_room, leave_room, disconnect
from flask_jwt_extended import decode_token

from models.user import User
from models import db
from services.group_service import is_group_member, group_room_name
from services.message_service import create_group_message


CONNECTED_USERS = {}


def _extract_token(auth_payload):
    if not auth_payload or not isinstance(auth_payload, dict):
        return None

    raw_token = auth_payload.get('token')
    if not raw_token or not isinstance(raw_token, str):
        return None

    if raw_token.startswith('Bearer '):
        return raw_token.split(' ', 1)[1].strip()

    return raw_token.strip()


def _emit_error(code, message):
    emit('group:error', {'code': code, 'message': message}, to=request.sid)


def _current_user_context():
    return CONNECTED_USERS.get(request.sid)


def register_socket_events(socketio):
    @socketio.on('connect')
    def handle_connect(auth):
        token = _extract_token(auth)
        if not token:
            return False

        try:
            decoded = decode_token(token)
            identity = decoded.get('sub')
            user_id = int(identity)
        except Exception:
            return False

        user = db.session.get(User, user_id)
        if not user:
            return False

        CONNECTED_USERS[request.sid] = {
            'user_id': user.id,
            'name': user.name,
        }

        emit(
            'socket:ready',
            {
                'user_id': user.id,
                'name': user.name,
            },
            to=request.sid,
        )

    @socketio.on('disconnect')
    def handle_disconnect():
        CONNECTED_USERS.pop(request.sid, None)

    @socketio.on('group:join')
    def handle_group_join(data):
        context = _current_user_context()
        if not context:
            _emit_error('AUTH_FAILED', '未授權的連線')
            disconnect()
            return

        group_id = (data or {}).get('group_id')
        if not group_id:
            _emit_error('INVALID_PAYLOAD', 'group_id 為必填')
            return

        try:
            group_id = int(group_id)
        except (TypeError, ValueError):
            _emit_error('INVALID_PAYLOAD', 'group_id 格式錯誤')
            return

        if not is_group_member(group_id, context['user_id']):
            _emit_error('NOT_MEMBER', '您不是該群組成員')
            return

        room = group_room_name(group_id)
        join_room(room)
        emit('group:joined', {'group_id': group_id}, to=request.sid)

    @socketio.on('group:leave')
    def handle_group_leave(data):
        context = _current_user_context()
        if not context:
            _emit_error('AUTH_FAILED', '未授權的連線')
            disconnect()
            return

        group_id = (data or {}).get('group_id')
        if not group_id:
            _emit_error('INVALID_PAYLOAD', 'group_id 為必填')
            return

        try:
            group_id = int(group_id)
        except (TypeError, ValueError):
            _emit_error('INVALID_PAYLOAD', 'group_id 格式錯誤')
            return

        room = group_room_name(group_id)
        leave_room(room)
        emit('group:left', {'group_id': group_id}, to=request.sid)

    @socketio.on('group:send-message')
    def handle_group_send_message(data):
        context = _current_user_context()
        if not context:
            _emit_error('AUTH_FAILED', '未授權的連線')
            disconnect()
            return

        payload = data or {}
        group_id = payload.get('group_id')
        content = (payload.get('content') or '').strip()

        if not group_id:
            _emit_error('INVALID_PAYLOAD', 'group_id 為必填')
            return
        if not content:
            _emit_error('INVALID_PAYLOAD', 'content 不可為空')
            return

        try:
            group_id = int(group_id)
        except (TypeError, ValueError):
            _emit_error('INVALID_PAYLOAD', 'group_id 格式錯誤')
            return

        if not is_group_member(group_id, context['user_id']):
            _emit_error('NOT_MEMBER', '您不是該群組成員')
            return

        try:
            message = create_group_message(group_id, context['user_id'], content)
        except ValueError as exc:
            _emit_error('INVALID_PAYLOAD', str(exc))
            return
        except Exception:
            db.session.rollback()
            _emit_error('SERVER_ERROR', '訊息發送失敗')
            return

        room = group_room_name(group_id)
        emit('group:new-message', message, to=room)
