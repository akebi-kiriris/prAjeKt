# backend/scripts/db

這層放資料庫初始化、migration 輔助與歷史資料遷移腳本，主要用於開發期維護或一次性資料處理。

## 目前腳本

- `init_db.py`
- `create_missing_tables.py`
- `safe_migrate.py`
- `migrate_sqlite_to_postgres.py`

## 這層應該負責什麼

- 開發期資料庫初始化輔助
- 舊資料庫結構補齊
- migration 升級前置檢查與安全執行
- SQLite -> PostgreSQL 歷史資料遷移

## 不應該放什麼

- Alembic migration revision
- 與資料庫無關的通用工具
