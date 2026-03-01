from models import db
from datetime import datetime

class Timeline(db.Model):
    __tablename__ = 'timelines'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    remark = db.Column(db.Text)
    deleted_at = db.Column(db.DateTime, nullable=True)  # None=正常, 有值=軟刪除時間
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Timeline {self.name}>'

class TaskFile(db.Model):
    __tablename__ = 'task_files'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.task_id'))
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    # 關聯（cascade 保證 Task 永久刪除時自動清除附件記錄）
    task = db.relationship('Task', backref=db.backref('files', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<TaskFile {self.filename}>'
