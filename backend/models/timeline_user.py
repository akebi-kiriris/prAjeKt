from models import db
from datetime import datetime

class TimelineUser(db.Model):
    __tablename__ = 'timeline_users'
    
    id = db.Column(db.Integer, primary_key=True)
    timeline_id = db.Column(db.Integer, db.ForeignKey('timelines.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.Integer, nullable=True)  # 0: 負責人, 1: 協作者
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 關聯
    timeline = db.relationship('Timeline', backref=db.backref('timeline_members', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('joined_timelines', lazy=True))
    
    # 複合唯一索引
    __table_args__ = (
        db.UniqueConstraint('timeline_id', 'user_id', name='_timeline_user_uc'),
    )
    
    def __repr__(self):
        return f'<TimelineUser timeline_id={self.timeline_id} user_id={self.user_id} role={self.role}>'
