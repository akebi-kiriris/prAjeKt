# backend/migrations

這層保存 Alembic / Flask-Migrate migration 與 migration 環境設定。

## 主要內容

- `env.py`: migration 執行環境
- `versions/`: 每次 schema 變更的 migration revision
- `script.py.mako`: migration 模板
- `alembic.ini` / `README`: Alembic 基本設定

## 這層應該負責什麼

- 資料表 schema 演進紀錄
- migration 執行設定
- revision 歷史保存

## 不應該放什麼

- 任意手寫的業務腳本
- 長期留存的資料修補腳本
- 與 migration 無關的 SQL 筆記

## 修改判斷

- model 欄位、索引、關聯改動後，通常要回來看這層
- 若是 migration 執行失敗或 revision mismatch，優先檢查這裡與 `safe_migrate.py`
- 大量資料回填或一次性修補，不一定要寫進 migration；先評估是否應獨立成腳本
