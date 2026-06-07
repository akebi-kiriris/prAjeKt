# backend/scripts

這層放後端維護型腳本，主要是一次性 backfill、舊資料庫初始化與診斷工具。

## 目錄分工

- `backfill/`: 舊資料補填腳本
- `db/`: 初始化 / 補表 / 舊 SQLite 維護腳本
- `diagnostics/`: 本地資料庫診斷腳本

## 這層應該負責什麼

- 一次性維護工具
- 遷移過程中的輔助腳本
- 開發期診斷與修補

## 不應該放什麼

- 長期主線業務邏輯
- HTTP route
- 正式 service / repository 程式碼

## 修改判斷

- 如果腳本只在某個維修、回填、檢查情境下才會用到，優先放這裡
- 若腳本已變成日常主線流程，再評估是否應回到 `backend/` 根層或整合進 service / migration
