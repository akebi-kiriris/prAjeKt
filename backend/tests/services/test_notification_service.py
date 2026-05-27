import pytest

from models import db
from models.notification import Notification
from models.user import User
from services.notification_service import (
    NotificationOperationError,
    delete_notification_for_user,
    get_notifications_for_user,
    get_unread_count_for_user,
    mark_all_notifications_as_read,
    mark_notification_as_read,
    notification_to_dict,
)



def test_notification_service_to_dict(app, user_factory):
    user = user_factory("notif-service@example.com", "notif_service_user")
    notif = Notification(
        user_id=user.id,
        type="task_assigned",
        title="Assigned",
        content="You have a new task",
        link="/tasks/1",
        is_read=False,
    )
    db.session.add(notif)
    db.session.commit()

    payload = notification_to_dict(notif)
    assert payload["title"] == "Assigned"
    assert payload["is_read"] is False
    assert payload["created_at"].endswith("Z")


def test_notification_service_operations(app, user_factory):
    user = user_factory("notif-ops@example.com", "notif_ops_user")
    n1 = Notification(
        user_id=user.id,
        type="task_assigned",
        title="n1",
        content="A",
        link="/tasks/1",
        is_read=False,
    )
    n2 = Notification(
        user_id=user.id,
        type="task_assigned",
        title="n2",
        content="B",
        link="/tasks/2",
        is_read=False,
    )
    db.session.add_all([n1, n2])
    db.session.commit()

    notifications = get_notifications_for_user(user.id)
    assert len(notifications) == 2
    assert get_unread_count_for_user(user.id) == 2

    mark_notification_as_read(n1.id, user.id)
    assert get_unread_count_for_user(user.id) == 1

    mark_all_notifications_as_read(user.id)
    assert get_unread_count_for_user(user.id) == 0

    delete_notification_for_user(n2.id, user.id)
    assert Notification.query.filter_by(id=n2.id).first() is None


def test_notification_service_not_found_errors(app, user_factory):
    user = user_factory("notif-err@example.com", "notif_err_user")

    with pytest.raises(NotificationOperationError) as read_exc:
        mark_notification_as_read(999999, user.id)
    assert read_exc.value.status_code == 404

    with pytest.raises(NotificationOperationError) as delete_exc:
        delete_notification_for_user(999999, user.id)
    assert delete_exc.value.status_code == 404
