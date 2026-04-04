from models import db
from models.time_utils import utcnow_naive


class GroupAISnapshot(db.Model):
    __tablename__ = 'group_ai_snapshots'

    snapshot_id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.group_id'), nullable=False, index=True)
    summary_json = db.Column(db.JSON, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow_naive, nullable=False)
    source_count = db.Column(db.Integer, default=0, nullable=False)
    model = db.Column(db.String(128))
    provider = db.Column(db.String(64))
    metadata_json = db.Column(db.JSON)

    def __repr__(self):
        return f'<GroupAISnapshot {self.snapshot_id}>'
