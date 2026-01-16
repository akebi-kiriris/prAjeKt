from models import db
from datetime import datetime

class TaskUser(db.Model):
    __tablename__ = 'task_users'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.task_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.Integer, nullable=True)  # 0: 負責人, 1: 協作者
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 關聯
    task = db.relationship('Task', backref=db.backref('task_members', lazy=True))
    user = db.relationship('User', backref=db.backref('assigned_tasks', lazy=True))
    
    # 複合唯一索引
    __table_args__ = (
        db.UniqueConstraint('task_id', 'user_id', name='_task_user_uc'),
    )
    
    def __repr__(self):
        return f'<TaskUser task_id={self.task_id} user_id={self.user_id} role={self.role}>'
