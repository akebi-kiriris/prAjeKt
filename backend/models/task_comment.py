from models import db
from datetime import datetime

class TaskComment(db.Model):
    __tablename__ = 'task_comments'
    
    comment_id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.task_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 關聯
    task = db.relationship('Task', backref=db.backref('comments', lazy=True))
    user = db.relationship('User', backref=db.backref('task_comments', lazy=True))
    
    def __repr__(self):
        return f'<TaskComment {self.comment_id} on Task {self.task_id}>'
