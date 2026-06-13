# Backend Scripts Backfill 目錄說明

`backend/scripts/backfill/` 用於存放舊資料補填腳本，讓歷史資料對齊新欄位、新關聯或新結構要求。

## 責任範圍

本目錄應負責以下內容：

1. 對既有資料做一次性補填
2. 協助歷史資料對齊新結構

以下內容不應放在本目錄：

1. 日常啟動流程
2. 正式 migration revision
3. 長期主線服務邏輯

## 維護原則

1. backfill 腳本應清楚標示用途與適用資料範圍。
2. 若腳本只是 schema 變更的一部分，應先評估是否應由 migration 處理。
