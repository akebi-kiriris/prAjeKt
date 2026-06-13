# Backend Scripts DB 目錄說明

`backend/scripts/db/` 用於存放資料庫初始化、migration 輔助與歷史資料遷移腳本，主要服務於開發期維護與一次性資料處理。

## 責任範圍

本目錄應負責以下內容：

1. 開發期資料庫初始化輔助
2. 舊資料庫結構補齊
3. migration 升級前置檢查與安全執行
4. 歷史資料庫遷移工具

以下內容不應放在本目錄：

1. Alembic migration revision
2. 與資料庫無關的通用工具

## 相鄰目錄邊界

1. schema 版本本身由 `backend/migrations/` 管理。
2. 一般維護或補填腳本若不以資料庫流程為主，應評估移至其他 scripts 子目錄。

## 維護原則

1. 腳本應清楚區分初始化、修復與遷移用途。
2. 若腳本依賴特定 migration 狀態，應在檔內或相關文件中註明。
