# backend/scripts/backfill

這層放舊資料補填腳本，用來把歷史資料補成符合新結構的狀態。

## 目前腳本

- `backfill_task_users.py`
- `backfill_timeline_users.py`

## 這層應該負責什麼

- 對既有資料做一次性補填
- 協助舊資料對齊新欄位或新關聯

## 不應該放什麼

- 日常啟動流程
- 正式 migration revision
- 長期主線服務邏輯
