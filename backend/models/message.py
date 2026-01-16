from models import db
from datetime import datetime

class Message(db.Model):
    __tablename__ = 'messages'
    
    message_id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.group_id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.Text)
    message_type = db.Column(db.String(20), default='text')  # text/image/file/system
    attachment_url = db.Column(db.String(500))  # 附件路徑
    is_deleted = db.Column(db.Boolean, default=False)  # 軟刪除
    reply_to = db.Column(db.Integer, db.ForeignKey('messages.message_id'))  # 回覆功能
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    edited_at = db.Column(db.DateTime)  # 編輯時間
    
    def __repr__(self):
        return f'<Message {self.message_id}>'

class MessageRead(db.Model):
    __tablename__ = 'message_reads'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.message_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    read_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MessageRead {self.id}>'
