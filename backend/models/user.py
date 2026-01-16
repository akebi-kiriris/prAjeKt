from models import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=True)  # 唯一用戶名（如 @john_doe）
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    avatar = db.Column(db.String(500))  # 頭像路徑
    bio = db.Column(db.Text)  # 個人簡介
    is_active = db.Column(db.Boolean, default=True)  # 帳號狀態
    last_login_at = db.Column(db.DateTime)  # 最後登入時間
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.email}>'
