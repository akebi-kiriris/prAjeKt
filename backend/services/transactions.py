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
    """Wrap DB transaction with standardized rollback and domain error mapping.

    參數:
        error_cls: Domain error class to re-raise.
        error_message: Fallback error message for unexpected exceptions.
        status_code: Fallback status code for unexpected exceptions.

    Yields:
        Transaction execution context.
    """
    try:
        yield
        db.session.commit()
    except error_cls:
        db.session.rollback()
        raise
    except Exception as exc:
        db.session.rollback()
        raise error_cls(error_message, status_code) from exc

