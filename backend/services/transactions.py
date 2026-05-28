from contextlib import contextmanager
from collections.abc import Generator
from typing import Type

from models import db


@contextmanager
def transaction(
    error_cls: Type[Exception],
    error_message: str,
    status_code: int = 500,
) -> Generator[None, None, None]:
    try:
        yield
        db.session.commit()
    except error_cls:
        db.session.rollback()
        raise
    except Exception as exc:
        db.session.rollback()
        raise error_cls(error_message, status_code) from exc
