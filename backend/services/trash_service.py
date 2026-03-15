import os


def trash_task_to_dict(task, user_id):
    return {
        'task_id': task.task_id,
        'name': task.name,
        'deleted_at': task.deleted_at.isoformat() + 'Z' if task.deleted_at else None,
        'end_date': task.end_date.isoformat() + 'Z' if task.end_date else None,
        'priority': task.priority,
        'is_owner': task.user_id == user_id,
    }


def trash_timeline_to_dict(timeline, user_id):
    return {
        'id': timeline.id,
        'name': timeline.name,
        'deleted_at': timeline.deleted_at.isoformat() + 'Z' if timeline.deleted_at else None,
        'start_date': timeline.start_date.isoformat() + 'Z' if timeline.start_date else None,
        'end_date': timeline.end_date.isoformat() + 'Z' if timeline.end_date else None,
        'is_owner': timeline.user_id == user_id,
    }


def remove_task_files(task):
    for task_file in task.files:
        if task_file.file_path and os.path.exists(task_file.file_path):
            os.remove(task_file.file_path)
