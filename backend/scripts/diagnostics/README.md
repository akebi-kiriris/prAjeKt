# backend/scripts/diagnostics

這層放資料庫與後端環境的診斷腳本。

## 目前腳本

- `check_tables.py`

## 這層應該負責什麼

- 檢查本地資料庫有哪些表與欄位
- 輔助排查遷移或舊資料不一致問題

## 不應該放什麼

- 正式 migration
- 主線啟動流程
- 一般業務程式碼
