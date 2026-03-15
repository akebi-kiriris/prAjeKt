def notification_to_dict(notification):
    return {
        'id': notification.id,
        'type': notification.type,
        'title': notification.title,
        'content': notification.content,
        'link': notification.link,
        'is_read': notification.is_read,
        'created_at': notification.created_at.isoformat() + 'Z' if notification.created_at else None,
    }
