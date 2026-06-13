# Backend Repositories 目錄說明

`backend/repositories/` 負責資料存取封裝。每個 repository 以特定資料模型或查詢主題為單位，集中管理查詢、寫入與 session 相關細節，避免 ORM 操作分散到 service 各處。

## 責任範圍

本目錄應負責以下內容：

1. 查詢、建立、更新、刪除資料
2. 常用查詢模式與資料抓取封裝
3. 與 session / transaction 配合的存取細節

以下內容不應放在本目錄：

1. 使用者流程與商業規則判斷
2. API response 組裝
3. agent tool envelope 或錯誤映射
4. LangGraph 狀態流轉

## 相鄰目錄邊界

1. 若需求是「資料怎麼查、怎麼存」，優先看本目錄。
2. 若需求是「什麼時候該查、該存或該拒絕」，通常屬於 `backend/services/`。
3. 若欄位或關聯變動，應同步檢查 `backend/models/` 與 `backend/migrations/`。

## 維護原則

1. repository 應保持為資料存取層，不承擔商業決策。
2. 重複出現的查詢邏輯應優先收斂到本目錄。
3. 若 repository 開始混入過多流程判斷，應回頭拆回 service 層。
