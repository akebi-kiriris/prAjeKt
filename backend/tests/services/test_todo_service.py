import pytest

from models import db
from models.todo import Todo
from models.user import User
from services.todo_service import (
    TodoOperationError,
    create_todo_for_user,
    find_unknown_fields as todo_find_unknown_fields,
    list_todos_for_user,
    soft_delete_todo_for_user,
    todo_to_dict,
    toggle_todo_for_user,
    update_todo_for_user,
)


def _create_user(email: str, username: str) -> User:
    user = User(
        name="Service Test User",
        username=username,
        email=email,
        password="hashed-password",
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_todo_service_helpers_and_serializer(app):
    unknown = todo_find_unknown_fields(
        {"title": "t", "content": "c", "bad": True},
        {"title", "content"},
    )
    assert unknown == ["bad"]

    user = _create_user("todo-service@example.com", "todo_service_user")
    todo = Todo(
        user_id=user.id,
        title="Todo title",
        content="Todo content",
        type="personal",
        priority=2,
    )
    db.session.add(todo)
    db.session.commit()

    payload = todo_to_dict(todo)
    assert payload["title"] == "Todo title"
    assert payload["priority"] == 2
    assert payload["created_at"].endswith("Z")


def test_todo_service_crud_operations(app):
    user = _create_user("todo-service-crud@example.com", "todo_service_crud_user")

    todo_id = create_todo_for_user(
        user.id,
        {
            "title": "Plan Sprint",
            "content": "Prepare sprint goals",
            "priority": 1,
            "deadline": "2026-04-30",
        },
    )

    listed = list_todos_for_user(user.id)
    assert any(item.id == todo_id for item in listed)

    update_todo_for_user(
        todo_id,
        user.id,
        {
            "title": "Plan Sprint Updated",
            "completed": True,
            "priority": 2,
        },
    )
    updated = db.session.get(Todo, todo_id)
    assert updated.title == "Plan Sprint Updated"
    assert updated.completed is True

    completed = toggle_todo_for_user(todo_id, user.id)
    assert completed is False

    soft_delete_todo_for_user(todo_id, user.id)
    assert db.session.get(Todo, todo_id).deleted_at is not None


def test_todo_service_validation_and_not_found_errors(app):
    user = _create_user("todo-service-error@example.com", "todo_service_error_user")

    with pytest.raises(TodoOperationError) as unknown_exc:
        create_todo_for_user(
            user.id,
            {
                "title": "A",
                "content": "B",
                "not_allowed": True,
            },
        )
    assert unknown_exc.value.status_code == 400

    todo_id = create_todo_for_user(
        user.id,
        {
            "title": "Valid",
            "content": "Valid content",
        },
    )

    with pytest.raises(TodoOperationError) as priority_exc:
        update_todo_for_user(todo_id, user.id, {"priority": 9})
    assert priority_exc.value.status_code == 400

    with pytest.raises(TodoOperationError) as missing_exc:
        update_todo_for_user(999999, user.id, {"title": "X"})
    assert missing_exc.value.status_code == 404
