from models import db
from datetime import datetime

class Todo(db.Model):
    __tablename__ = 'todos'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50))
    deadline = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False)
    
    # 新增欄位
    priority = db.Column(db.Integer, default=2)  # 1:高 2:中 3:低
    order = db.Column(db.Integer)  # 自訂排序
    completed_at = db.Column(db.DateTime)  # 完成時間
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Todo {self.title}>'
