PROFILE_UPDATE_ALLOWED_FIELDS = {
    'name',
    'username',
    'phone',
    'email',
    'avatar',
    'bio',
    'current_password',
    'new_password',
}


def find_unknown_fields(payload, allowed_fields):
    return sorted(set(payload.keys()) - allowed_fields)


def profile_to_dict(user):
    return {
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email,
        'phone': user.phone,
        'avatar': user.avatar,
        'bio': user.bio,
        'created_at': user.created_at.isoformat() + 'Z' if user.created_at else None,
    }


def search_user_to_dict(user):
    return {
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email,
    }
