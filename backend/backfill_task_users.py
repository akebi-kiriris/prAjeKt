"""
補填 task_users 記錄
對每個 tasks 記錄，若其 user_id 沒有對應的 task_user(role=0)，則自動插入。
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from models.task import Task
from models.task_user import TaskUser

app = create_app()

with app.app_context():
    tasks = Task.query.all()
    inserted = 0
    skipped = 0

    for task in tasks:
        existing = TaskUser.query.filter_by(
            task_id=task.task_id,
            user_id=task.user_id
        ).first()
        if existing:
            skipped += 1
        else:
            db.session.add(TaskUser(
                task_id=task.task_id,
                user_id=task.user_id,
                role=0
            ))
            inserted += 1

    db.session.commit()
    print(f"完成！補填 {inserted} 筆，跳過 {skipped} 筆（已有記錄）")
