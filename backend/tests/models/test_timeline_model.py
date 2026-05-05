import pytest
from sqlalchemy.exc import IntegrityError

from models import db
from models.timeline import Timeline
from models.timeline_user import TimelineUser
from tests.models.helpers import create_user


def test_timeline_user_unique_constraint(app):
    owner = create_user("timeline-owner@example.com", username="timeline_owner")

    timeline = Timeline(user_id=owner.id, name="Timeline With Members")
    db.session.add(timeline)
    db.session.commit()

    first = TimelineUser(timeline_id=timeline.id, user_id=owner.id, role=0)
    db.session.add(first)
    db.session.commit()

    duplicated = TimelineUser(timeline_id=timeline.id, user_id=owner.id, role=1)
    db.session.add(duplicated)

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()


def test_delete_timeline_cascades_timeline_members(app):
    owner = create_user("timeline-cascade-owner@example.com", username="timeline_c_owner")
    member = create_user("timeline-cascade-member@example.com", username="timeline_c_member")

    timeline = Timeline(user_id=owner.id, name="Timeline Cascade")
    db.session.add(timeline)
    db.session.commit()

    db.session.add_all(
        [
            TimelineUser(timeline_id=timeline.id, user_id=owner.id, role=0),
            TimelineUser(timeline_id=timeline.id, user_id=member.id, role=1),
        ]
    )
    db.session.commit()

    db.session.delete(timeline)
    db.session.commit()

    assert TimelineUser.query.filter_by(timeline_id=timeline.id).count() == 0
