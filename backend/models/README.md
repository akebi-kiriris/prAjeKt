# Backend Models 目錄說明

`backend/models/` 定義 SQLAlchemy ORM model，是資料表結構、欄位與關聯在程式中的對應層。

## 責任範圍

本目錄應負責以下內容：

1. 資料表欄位定義
2. model 關聯設定
3. 與資料結構直接相關的輕量 helper

以下內容不應放在本目錄：

1. 商業流程判斷
2. HTTP response 組裝
3. agent tool 流程邏輯
4. 大量跨 model 協調

## 相鄰目錄邊界

1. 若問題是欄位、關聯或資料結構本身，優先看本目錄。
2. 若問題是何時建立、更新或拒絕資料，通常應回到 `backend/services/`。
3. 欄位或關聯異動時，應同步檢查 `backend/migrations/`、`backend/repositories/` 與相關契約。

## 維護原則

1. model 應聚焦在資料結構，不承擔複雜流程控制。
2. 結構變更需搭配 migration 與存取層一起檢查。
3. 若 helper 已需要依賴大量外部狀態，通常應往 service 層移動。
