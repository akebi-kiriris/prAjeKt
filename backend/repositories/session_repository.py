from models import db
from typing import Any


def add_entity(entity: Any) -> None:
    db.session.add(entity)


def delete_entity(entity: Any) -> None:
    db.session.delete(entity)


def flush_session() -> None:
    db.session.flush()
