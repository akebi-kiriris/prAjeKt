from models import db
from datetime import datetime

class Group(db.Model):
    __tablename__ = 'groups'
    
    group_id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(200), nullable=False)
    group_type = db.Column(db.String(50), default='task')
    group_inviteCode = db.Column(db.String(10), unique=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # 建立者
    description = db.Column(db.Text)  # 群組描述
    avatar = db.Column(db.String(500))  # 群組頭像
    is_active = db.Column(db.Boolean, default=True)  # 是否啟用
    max_members = db.Column(db.Integer, default=50)  # 成員上限
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Group {self.group_name}>'

class GroupMember(db.Model):
    __tablename__ = 'group_members'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.group_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<GroupMember {self.id}>'
