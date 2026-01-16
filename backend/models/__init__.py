from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 導入所有模型
from models.user import User
from models.group import Group, GroupMember
from models.message import Message, MessageRead
from models.task import Task
from models.timeline import Timeline, TaskFile
from models.todo import Todo
from models.task_comment import TaskComment
from models.task_user import TaskUser
from models.timeline_user import TimelineUser
from models.notification import Notification
from models.activity_log import ActivityLog

__all__ = [
    'db',
    'User',
    'Group', 'GroupMember',
    'Message', 'MessageRead',
    'Task', 'TaskFile',
    'Timeline',
    'Todo',
    'TaskComment',
    'TaskUser',
    'TimelineUser',
    'Notification',
    'ActivityLog'
]
