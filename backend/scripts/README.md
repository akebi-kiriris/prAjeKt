# Backend Scripts 目錄說明

`backend/scripts/` 存放後端維護型腳本，主要用於一次性 backfill、資料庫初始化輔助與環境診斷。

## 子目錄分工

1. `backfill/`
   - 舊資料補填腳本。
2. `db/`
   - 初始化、補表、migration 輔助與歷史資料遷移腳本。
3. `diagnostics/`
   - 本地資料庫與後端環境診斷腳本。

## 責任範圍

本目錄應負責以下內容：

1. 一次性維護工具
2. 遷移與修補過程中的輔助腳本
3. 開發期診斷與檢查工具

以下內容不應放在本目錄：

1. 長期主線業務邏輯
2. HTTP route
3. 正式 service / repository 程式碼

## 相鄰目錄邊界

1. 可被產品主線呼叫的業務邏輯應放 `backend/services/`，不要藏在 scripts。
2. schema revision 與正式資料庫演進應放 `backend/migrations/`。
3. 單純診斷用腳本放 `diagnostics/`，一次性資料補填放 `backfill/`，資料庫初始化或 migration 輔助放 `db/`。

## 維護原則

1. 腳本應有明確用途與適用情境，避免成為根層雜項集合。
2. 若腳本已變成日常主線流程，應重新評估是否整合回正式程式碼結構。
3. 與 schema 版本直接相關的內容，應優先由 `backend/migrations/` 管理。
