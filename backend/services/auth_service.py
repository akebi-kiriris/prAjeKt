from werkzeug.security import check_password_hash, generate_password_hash
from models import db
from models.user import User
from repositories.auth_repository import get_user_by_email, get_user_by_id, get_user_by_username


class AuthOperationError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def auth_user_to_dict(user):
    return {
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email,
    }


def current_user_to_dict(user):
    return {
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email,
        'phone': user.phone,
    }


def register_user(data):
    name = data.get('name')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')

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
        db.session.add(new_user)
        db.session.commit()
        return new_user.id
    except Exception as exc:
        db.session.rollback()
        raise AuthOperationError('註冊失敗，請稍後再試', 500) from exc


def authenticate_user(email, password):
    if not email or not password:
        raise AuthOperationError('請提供 email 和密碼', 400)

    user = get_user_by_email(email)
    if not user or not check_password_hash(user.password, password):
        raise AuthOperationError('帳號或密碼錯誤', 401)

    return user


def get_current_user_or_404(user_id):
    user = get_user_by_id(user_id)
    if not user:
        raise AuthOperationError('使用者不存在', 404)
    return user
