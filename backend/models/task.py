from models import db
from datetime import datetime

class Task(db.Model):
    __tablename__ = 'tasks'
    
    task_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    timeline_id = db.Column(db.Integer, db.ForeignKey('timelines.id'))
    task_remark = db.Column(db.Text)
    isWork = db.Column(db.Integer, default=0)
    
    # 新增欄位
    assistant = db.Column(db.String(255))  # 協助者
    priority = db.Column(db.Integer, default=2)  # 1:高 2:中 3:低
    status = db.Column(db.String(20), default='pending')  # pending/in_progress/review/completed/cancelled
    tags = db.Column(db.String(255))  # 標籤，逗號分隔
    estimated_hours = db.Column(db.Float)  # 預估工時
    actual_hours = db.Column(db.Float)  # 實際工時
    
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Task {self.name}>'
