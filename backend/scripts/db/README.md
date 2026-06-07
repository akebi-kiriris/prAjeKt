# backend/scripts/db

這層放舊 SQLite 時代遺留的初始化與補表腳本，主要用於開發期維護或歷史資料處理。

## 目前腳本

- `init_db.py`
- `create_missing_tables.py`

## 這層應該負責什麼

- 開發期資料庫初始化輔助
- 舊資料庫結構補齊

## 不應該放什麼

- Alembic migration revision
- 正式部署主線腳本
- 與資料庫無關的通用工具
