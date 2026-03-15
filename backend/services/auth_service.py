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
