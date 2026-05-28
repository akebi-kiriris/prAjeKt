from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.exc import IntegrityError
from models.user import User
from typing import Any
from repositories.auth_repository import get_user_by_email, get_user_by_id, get_user_by_username
from repositories.session_repository import add_entity
from services.transactions import transaction


class AuthOperationError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def auth_user_to_dict(user: User) -> dict[str, Any]:
    return {
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email,
    }


def current_user_to_dict(user: User) -> dict[str, Any]:
    return {
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email,
        'phone': user.phone,
    }


def register_user(data: dict[str, Any]) -> int:
    name = (data.get('name') or '').strip()
    username = data.get('username')
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')
    phone = data.get('phone')
    username = username.strip() if isinstance(username, str) and username.strip() else None
    phone = phone.strip() if isinstance(phone, str) and phone.strip() else None

    if not all([name, email, password]):
        raise AuthOperationError('缺少必要欄位', 400)

    if get_user_by_email(email):
        raise AuthOperationError('此 email 已被註冊', 409)

    if username and get_user_by_username(username):
        raise AuthOperationError('此用戶名已被使用', 409)

    new_user = User(
        name=name,
        username=username if username else None,
        email=email,
        password=generate_password_hash(password),
        phone=phone,
    )

    try:
        with transaction(AuthOperationError, '註冊失敗，請稍後再試'):
            add_entity(new_user)
        return new_user.id
    except AuthOperationError as err:
        cause = getattr(err, '__cause__', None)
        if isinstance(cause, IntegrityError):
            error_message = str(getattr(cause, 'orig', cause)).lower()
            if 'username' in error_message:
                raise AuthOperationError('此用戶名已被使用', 409) from cause
            if 'email' in error_message:
                raise AuthOperationError('此 email 已被註冊', 409) from cause
            raise AuthOperationError('帳號資料重複，請確認後再試', 409) from cause
        raise


def authenticate_user(email: str, password: str) -> User:
    normalized_email = email.strip().lower() if isinstance(email, str) else ''
    if not normalized_email or not password:
        raise AuthOperationError('請提供 email 和密碼', 400)

    user = get_user_by_email(normalized_email)
    if not user or not check_password_hash(user.password, password):
        raise AuthOperationError('帳號或密碼錯誤', 401)

    return user


def get_current_user_or_404(user_id: int) -> User:
    user = get_user_by_id(user_id)
    if not user:
        raise AuthOperationError('使用者不存在', 404)
    return user
