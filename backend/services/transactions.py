from contextlib import contextmanager

from models import db


@contextmanager
def transaction(error_cls, error_message, status_code=500):
    try:
        yield
        db.session.commit()
    except error_cls:
        db.session.rollback()
        raise
    except Exception as exc:
        db.session.rollback()
        raise error_cls(error_message, status_code) from exc
