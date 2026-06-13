# Backend Migrations 目錄說明

`backend/migrations/` 保存 Alembic / Flask-Migrate 的 schema 版本紀錄與 migration 執行設定。

## 責任範圍

本目錄應負責以下內容：

1. 資料表 schema 演進紀錄
2. migration 執行環境與設定
3. revision 歷史保存

以下內容不應放在本目錄：

1. 任意手寫的業務腳本
2. 長期留存的資料修補腳本
3. 與 migration 無關的 SQL 筆記

## 相鄰目錄邊界

1. 欄位、索引或關聯改動後，通常需要同步檢查本目錄。
2. 若是 revision mismatch 或升級失敗，應一併檢查 `backend/scripts/db/` 的相關輔助腳本。
3. 一次性資料回填或修補，通常更適合放在 `backend/scripts/`。

## 維護原則

1. migration 應聚焦在 schema 變更，而非承擔長期資料修補。
2. revision 歷史應保持可追蹤，避免混入與 schema 無關的內容。
