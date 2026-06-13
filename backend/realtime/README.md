# Backend Realtime 目錄說明

`backend/realtime/` 負責 Socket.IO 即時事件與連線邏輯，處理房間、廣播、即時訊息與相關事件路由。

## 責任範圍

本目錄應負責以下內容：

1. Socket event handler
2. 房間與連線狀態處理
3. 即時訊息與事件路由

以下內容不應放在本目錄：

1. 大量核心商業邏輯
2. 分散的資料庫查詢細節
3. HTTP API 行為

## 相鄰目錄邊界

1. 若問題只出現在 WebSocket、即時聊天或廣播行為，優先看本目錄。
2. 若問題涉及權限、資料寫入或商業規則，通常應回到 `backend/services/` 或 `backend/blueprints/`。

## 維護原則

1. 即時事件層應保持為傳遞與連線邊界，不承擔過多 domain 流程。
2. 與 HTTP API 共用的商業規則應集中在 service 層維護。
