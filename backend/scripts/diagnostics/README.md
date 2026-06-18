# Backend Scripts Diagnostics 目錄說明

`backend/scripts/diagnostics/` 用於存放資料庫與後端環境的診斷腳本，協助排查表結構、遷移狀態與本地環境異常。

## 責任範圍

本目錄應負責以下內容：

1. 檢查資料庫表與欄位狀態
2. 輔助排查遷移或歷史資料不一致問題
3. 協助定位本地後端環境異常

以下內容不應放在本目錄：

1. 正式 migration
2. 主線啟動流程
3. 一般業務程式碼

## 相鄰目錄邊界

1. 會修改資料的補填流程應放 `backend/scripts/backfill/` 或正式 migration。
2. schema 版本演進放 `backend/migrations/`。
3. service 行為驗證應放 `backend/tests/`，不要用診斷腳本取代測試。

## 維護原則

1. 診斷腳本應聚焦在檢查與報告，不混入長期修補流程。
2. 若腳本已具備固定修復作用，應評估是否改放其他更適合的目錄。
