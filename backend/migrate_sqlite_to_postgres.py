#!/usr/bin/env python
"""Migrate local data from SQLite to PostgreSQL.

Usage:
  python migrate_sqlite_to_postgres.py
  python migrate_sqlite_to_postgres.py --sqlite-path instance/prajekt.db --force
"""

from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values


TABLE_ORDER = [
    'users',
    'groups',
    'timelines',
    'tasks',
    'todos',
    'activity_logs',
    'group_members',
    'messages',
    'message_reads',
    'notifications',
    'timeline_users',
    'task_users',
    'task_comments',
    'task_files',
    'subtasks',
]

SKIP_TABLES = {'alembic_version'}


def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def get_sqlite_tables(cur: sqlite3.Cursor) -> list[str]:
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    return [r[0] for r in cur.fetchall()]


def get_pg_tables(cur) -> list[str]:
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
    return [r[0] for r in cur.fetchall()]


def get_sqlite_columns(cur: sqlite3.Cursor, table: str) -> list[str]:
    cur.execute(f"PRAGMA table_info({qident(table)})")
    return [row[1] for row in cur.fetchall()]


def get_pg_columns(cur, table: str) -> list[str]:
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s
        ORDER BY ordinal_position
        """,
        (table,),
    )
    return [row[0] for row in cur.fetchall()]


def get_pg_column_types(cur, table: str) -> dict[str, str]:
    cur.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s
        ORDER BY ordinal_position
        """,
        (table,),
    )
    return {row[0]: row[1] for row in cur.fetchall()}


def get_table_count_sqlite(cur: sqlite3.Cursor, table: str) -> int:
    cur.execute(f"SELECT COUNT(*) FROM {qident(table)}")
    return int(cur.fetchone()[0])


def get_table_count_pg(cur, table: str) -> int:
    cur.execute(f"SELECT COUNT(*) FROM {qident(table)}")
    return int(cur.fetchone()[0])


def get_primary_key_columns(cur, table: str) -> list[str]:
    cur.execute(
        """
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        WHERE tc.table_schema='public'
          AND tc.table_name=%s
          AND tc.constraint_type='PRIMARY KEY'
        ORDER BY kcu.ordinal_position
        """,
        (table,),
    )
    return [r[0] for r in cur.fetchall()]


def is_integer_column(cur, table: str, column: str) -> bool:
    cur.execute(
        """
        SELECT data_type
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s AND column_name=%s
        """,
        (table, column),
    )
    row = cur.fetchone()
    return bool(row and row[0] in {'smallint', 'integer', 'bigint'})


def reset_sequence_if_needed(cur, table: str) -> None:
    pk_cols = get_primary_key_columns(cur, table)
    if len(pk_cols) != 1:
        return

    pk_col = pk_cols[0]
    if not is_integer_column(cur, table, pk_col):
        return

    cur.execute("SELECT pg_get_serial_sequence(%s, %s)", (f'public.{table}', pk_col))
    seq_row = cur.fetchone()
    seq_name = seq_row[0] if seq_row else None
    if not seq_name:
        return

    q_table = qident(table)
    q_pk = qident(pk_col)
    cur.execute(
        f"""
        SELECT setval(
            %s,
            COALESCE((SELECT MAX({q_pk}) FROM {q_table}), 1),
            (SELECT COUNT(*) > 0 FROM {q_table})
        )
        """,
        (seq_name,),
    )


def normalize_pg_dsn(dsn: str) -> str:
    # SQLAlchemy URL: postgresql+psycopg2://... -> psycopg2 URL: postgresql://...
    return dsn.replace('postgresql+psycopg2://', 'postgresql://', 1)


def ordered_tables(common_tables: set[str]) -> list[str]:
    ordered = [t for t in TABLE_ORDER if t in common_tables]
    remaining = sorted(common_tables - set(ordered))
    return ordered + remaining


def normalize_value(value, data_type: str):
    if value is None:
        return None

    if data_type == 'boolean':
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            low = value.strip().lower()
            if low in {'1', 't', 'true', 'y', 'yes'}:
                return True
            if low in {'0', 'f', 'false', 'n', 'no'}:
                return False
    return value


def migrate(sqlite_path: Path, pg_dsn: str, force: bool, skip_if_not_empty: bool) -> None:
    if not sqlite_path.exists():
        raise FileNotFoundError(f'SQLite file not found: {sqlite_path}')

    sqlite_conn = sqlite3.connect(str(sqlite_path))
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    pg_conn = psycopg2.connect(normalize_pg_dsn(pg_dsn))
    pg_conn.autocommit = False
    pg_cur = pg_conn.cursor()

    try:
        sqlite_tables = set(get_sqlite_tables(sqlite_cur))
        pg_tables = set(get_pg_tables(pg_cur))
        common_tables = (sqlite_tables & pg_tables) - SKIP_TABLES

        if not common_tables:
            print('No common business tables found between SQLite and PostgreSQL.')
            return

        # Safety check: prevent accidental duplicate migration
        non_empty_pg = []
        for table in sorted(common_tables):
            if get_table_count_pg(pg_cur, table) > 0:
                non_empty_pg.append(table)

        if non_empty_pg and not force:
            message = (
                'Target PostgreSQL already contains data in tables: '
                + ', '.join(non_empty_pg)
                + '. Re-run with --force if you really want to append.'
            )
            if skip_if_not_empty:
                print('Skip migration:', message)
                return
            raise RuntimeError(message)

        print('Starting migration SQLite -> PostgreSQL')
        print(f'SQLite: {sqlite_path}')
        print('PostgreSQL: [connected]')

        summary = []
        for table in ordered_tables(common_tables):
            sqlite_cols = get_sqlite_columns(sqlite_cur, table)
            pg_cols = get_pg_columns(pg_cur, table)
            pg_types = get_pg_column_types(pg_cur, table)
            cols = [c for c in sqlite_cols if c in pg_cols]

            if not cols:
                summary.append((table, 0, 0, 'skip(no common columns)'))
                continue

            q_cols = ', '.join(qident(c) for c in cols)
            sqlite_cur.execute(f"SELECT {q_cols} FROM {qident(table)}")
            rows = sqlite_cur.fetchall()

            if not rows:
                summary.append((table, 0, 0, 'ok(empty)'))
                continue

            values = [
                tuple(normalize_value(r[c], pg_types.get(c, '')) for c in cols)
                for r in rows
            ]
            insert_sql = f"INSERT INTO {qident(table)} ({q_cols}) VALUES %s"
            execute_values(pg_cur, insert_sql, values, page_size=500)

            reset_sequence_if_needed(pg_cur, table)

            summary.append((table, len(rows), len(rows), 'ok'))

        pg_conn.commit()

        print('\nMigration summary:')
        for table, src_n, dst_n, status in summary:
            print(f'- {table}: sqlite_rows={src_n}, inserted={dst_n}, status={status}')

        print('\nDone.')

    except Exception:
        pg_conn.rollback()
        raise
    finally:
        sqlite_cur.close()
        sqlite_conn.close()
        pg_cur.close()
        pg_conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description='Migrate SQLite data to PostgreSQL')
    parser.add_argument(
        '--sqlite-path',
        default='instance/prajekt.db',
        help='Path to SQLite DB file (default: instance/prajekt.db)',
    )
    parser.add_argument(
        '--pg-dsn',
        default=os.getenv('DATABASE_URL', ''),
        help='PostgreSQL DSN (default: DATABASE_URL env)',
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Allow migration even if target PostgreSQL already has rows',
    )
    parser.add_argument(
        '--skip-if-not-empty',
        action='store_true',
        help='Skip migration gracefully when target PostgreSQL already has rows',
    )
    args = parser.parse_args()

    if not args.pg_dsn:
        raise RuntimeError('DATABASE_URL is empty. Set env or pass --pg-dsn.')

    migrate(Path(args.sqlite_path), args.pg_dsn, args.force, args.skip_if_not_empty)


if __name__ == '__main__':
    main()
