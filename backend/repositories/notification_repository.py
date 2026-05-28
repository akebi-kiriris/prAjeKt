from models.notification import Notification


def list_notifications_for_user(user_id: int, limit: int = 50) -> list[Notification]:
    return (
        Notification.query
        .filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )


def count_unread_notifications_for_user(user_id: int) -> int:
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()


def get_notification_for_user(notification_id: int, user_id: int) -> Notification | None:
    return Notification.query.filter_by(id=notification_id, user_id=user_id).first()


def mark_all_unread_notifications_as_read(user_id: int) -> int:
    return Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
