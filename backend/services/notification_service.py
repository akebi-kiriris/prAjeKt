from repositories.notification_repository import (
    count_unread_notifications_for_user,
    get_notification_for_user,
    list_notifications_for_user,
    mark_all_unread_notifications_as_read,
)
from repositories.session_repository import delete_entity
from services.transactions import transaction


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

    with transaction(NotificationOperationError, '標記通知失敗，請稍後再試'):
        notification.is_read = True


def mark_all_notifications_as_read(user_id):
    with transaction(NotificationOperationError, '標記全部通知失敗，請稍後再試'):
        mark_all_unread_notifications_as_read(user_id)


def delete_notification_for_user(notification_id, user_id):
    notification = get_notification_for_user(notification_id, user_id)
    if not notification:
        raise NotificationOperationError('找不到通知', 404)

    with transaction(NotificationOperationError, '刪除通知失敗，請稍後再試'):
        delete_entity(notification)
