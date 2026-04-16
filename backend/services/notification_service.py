from models import db
from repositories.notification_repository import (
    count_unread_notifications_for_user,
    get_notification_for_user,
    list_notifications_for_user,
    mark_all_unread_notifications_as_read,
)


class NotificationOperationError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


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


def get_notifications_for_user(user_id, limit=50):
    return list_notifications_for_user(user_id, limit=limit)


def get_unread_count_for_user(user_id):
    return count_unread_notifications_for_user(user_id)


def mark_notification_as_read(notification_id, user_id):
    notification = get_notification_for_user(notification_id, user_id)
    if not notification:
        raise NotificationOperationError('找不到通知', 404)

    notification.is_read = True
    db.session.commit()


def mark_all_notifications_as_read(user_id):
    mark_all_unread_notifications_as_read(user_id)
    db.session.commit()


def delete_notification_for_user(notification_id, user_id):
    notification = get_notification_for_user(notification_id, user_id)
    if not notification:
        raise NotificationOperationError('找不到通知', 404)

    db.session.delete(notification)
    db.session.commit()
