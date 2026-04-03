"""Run Flask-Migrate safely for both fresh and pre-populated databases.

If app tables already exist but alembic_version is missing, we stamp a known
legacy baseline revision first to prevent duplicate-table failures while still
allowing newer migrations to run.
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Set

from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv


APP_TABLE_SENTINELS: Set[str] = {
    "users",
    "groups",
    "tasks",
    "timelines",
    "todos",
    "messages",
}

# Legacy databases may already contain app tables created outside Alembic.
# Stamp to this known baseline, then run upgrade so newer migrations still apply.
LEGACY_BASELINE_REVISION = "c1d2e3f4a5bb"


def _load_db_env() -> None:
    if os.path.exists(".env.local"):
        load_dotenv(".env.local", override=True)
    elif os.path.exists(".env"):
        load_dotenv(".env", override=False)


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return "postgresql://" + database_url[len("postgres://") :]
    return database_url


def _should_stamp_legacy_baseline() -> bool:
    _load_db_env()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[safe_migrate] DATABASE_URL not set, skip stamp precheck.")
        return False

    database_url = _normalize_database_url(database_url)
    engine = create_engine(database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            inspector = inspect(conn)
            tables = set(inspector.get_table_names())
    except Exception as exc:
        print(f"[safe_migrate] Precheck failed, continue with normal upgrade: {exc}")
        return False
    finally:
        engine.dispose()

    has_alembic_version = "alembic_version" in tables
    has_existing_app_tables = any(name in tables for name in APP_TABLE_SENTINELS)

    if has_existing_app_tables and not has_alembic_version:
        print(
            "[safe_migrate] Existing app tables detected without alembic_version; "
            f"will stamp baseline {LEGACY_BASELINE_REVISION} before upgrade."
        )
        return True

    return False


def _run_flask_db(*args: str) -> int:
    command = [sys.executable, "-m", "flask", "--app", "app.py", "db", *args]
    print("[safe_migrate] Running:", " ".join(command))
    result = subprocess.run(command, check=False)
    return result.returncode


def main() -> int:
    if _should_stamp_legacy_baseline():
        stamp_code = _run_flask_db("stamp", LEGACY_BASELINE_REVISION)
        if stamp_code != 0:
            print("[safe_migrate] Stamp baseline revision failed.")
            return stamp_code

    upgrade_code = _run_flask_db("upgrade")
    if upgrade_code != 0:
        print("[safe_migrate] Upgrade failed.")
    return upgrade_code


if __name__ == "__main__":
    raise SystemExit(main())
