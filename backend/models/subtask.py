from models import db
from datetime import datetime

class Subtask(db.Model):
    """子任務模型"""
    __tablename__ = 'subtasks'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.task_id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)

    # 關聯（cascade 保證 Task 永久刪除時自動清除子任務）
    task = db.relationship('Task', backref=db.backref('subtasks', lazy=True, cascade='all, delete-orphan'))
    completed = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)  # 排序順序
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Subtask {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'name': self.name,
            'completed': self.completed,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
