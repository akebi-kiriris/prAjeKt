from models.todo import Todo


def get_active_todo_by_id_for_user(todo_id: int, user_id: int) -> Todo | None:
    return Todo.query.filter_by(id=todo_id, user_id=user_id).filter(Todo.deleted_at.is_(None)).first()


def list_active_todos_for_user(user_id: int) -> list[Todo]:
    return (
        Todo.query
        .filter_by(user_id=user_id)
        .filter(Todo.deleted_at.is_(None))
        .order_by(Todo.completed, Todo.deadline)
        .all()
    )
