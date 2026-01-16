from models import db
from datetime import datetime

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # created/updated/deleted/completed
    entity_type = db.Column(db.String(50), nullable=False)  # task/message/todo/timeline/group
    entity_id = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)  # "更新了任務「XXX」的狀態為已完成"
    ip_address = db.Column(db.String(45))  # IPv4/IPv6
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 關聯
    user = db.relationship('User', backref=db.backref('activity_logs', lazy=True))
    
    # 複合索引
    __table_args__ = (
        db.Index('idx_entity', 'entity_type', 'entity_id'),
        db.Index('idx_user_date', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f'<ActivityLog {self.action} {self.entity_type} by User {self.user_id}>'
