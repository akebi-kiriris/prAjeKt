from models import db


def add_entity(entity):
    db.session.add(entity)


def delete_entity(entity):
    db.session.delete(entity)


def flush_session():
    db.session.flush()
