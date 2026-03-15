from models.todo import Todo

TODO_CREATE_ALLOWED_FIELDS = {'title', 'content', 'type', 'deadline', 'priority'}
TODO_UPDATE_ALLOWED_FIELDS = {'title', 'content', 'type', 'deadline', 'priority', 'completed'}


def find_unknown_fields(payload, allowed_fields):
    return sorted(set(payload.keys()) - allowed_fields)


def todo_to_dict(todo: Todo):
    return {
        'id': todo.id,
        'title': todo.title,
        'content': todo.content,
        'type': todo.type,
        'deadline': todo.deadline.isoformat() + 'Z' if todo.deadline else None,
        'completed': todo.completed,
        'priority': todo.priority,
        'created_at': todo.created_at.isoformat() + 'Z' if todo.created_at else None,
        'updated_at': todo.updated_at.isoformat() + 'Z' if todo.updated_at else None,
    }
