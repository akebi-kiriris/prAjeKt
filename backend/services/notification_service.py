from repositories.notification_repository import (
    count_unread_notifications_for_user,
    get_notification_for_user,
    list_notifications_for_user,
    mark_all_unread_notifications_as_read,
)
from repositories.session_repository import delete_entity
from services.transactions import transaction
from models.notification import Notification
from typing import Any


class NotificationOperationError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def notification_to_dict(notification: Notification) -> dict[str, Any]:
    """序列化通知模型。

    參數:
        notification: 通知模型實例。

    回傳:
        API 回應用通知 payload。
    """
    return {
        'id': notification.id,
        'type': notification.type,
        'title': notification.title,
        'content': notification.content,
        'link': notification.link,
        'is_read': notification.is_read,
        'created_at': notification.created_at.isoformat() + 'Z' if notification.created_at else None,
    }


def get_notifications_for_user(user_id: int, limit: int = 50) -> list[Notification]:
    """取得使用者最新通知清單。

    參數:
        user_id: 目標使用者 id。
        limit: 最大回傳筆數。

    回傳:
        依建立時間倒序的通知模型列表。
    """
    return list_notifications_for_user(user_id, limit=limit)


def get_unread_count_for_user(user_id: int) -> int:
    """計算使用者未讀通知數量。

    參數:
        user_id: 目標使用者 id。

    回傳:
        未讀通知數量。
    """
    return count_unread_notifications_for_user(user_id)


def mark_notification_as_read(notification_id: int, user_id: int) -> None:
    """將單筆通知標記為已讀。

    參數:
        notification_id: 通知 id。
        user_id: 通知擁有者使用者 id。

    例外:
        NotificationOperationError: 通知不存在或交易失敗。
    """
    notification = get_notification_for_user(notification_id, user_id)
    if not notification:
        raise NotificationOperationError('找不到通知', 404)

    with transaction(NotificationOperationError, '標記通知失敗，請稍後再試'):
        notification.is_read = True


def mark_all_notifications_as_read(user_id: int) -> None:
    """將使用者所有未讀通知標記為已讀。

    參數:
        user_id: 通知擁有者使用者 id。

    例外:
        NotificationOperationError: 交易失敗。
    """
    with transaction(NotificationOperationError, '標記全部通知失敗，請稍後再試'):
        mark_all_unread_notifications_as_read(user_id)


def delete_notification_for_user(notification_id: int, user_id: int) -> None:
    """刪除使用者單筆通知。

    參數:
        notification_id: 通知 id。
        user_id: 通知擁有者使用者 id。

    例外:
        NotificationOperationError: 通知不存在或刪除交易失敗。
    """
    notification = get_notification_for_user(notification_id, user_id)
    if not notification:
        raise NotificationOperationError('找不到通知', 404)

    with transaction(NotificationOperationError, '刪除通知失敗，請稍後再試'):
        delete_entity(notification)

