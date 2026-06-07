# backend/realtime

這層負責 Socket.IO 即時事件，處理群組聊天、即時更新與相關連線邏輯。

## 主要檔案

- `socket_events.py`: 事件註冊、連線、房間、訊息傳遞與 fallback 邏輯

## 這層應該負責什麼

- Socket event handler
- 房間 / 連線狀態處理
- 即時訊息路由

## 不應該放什麼

- 大量核心商業邏輯
- 資料庫查詢細節散落
- HTTP API 行為

## 修改判斷

- 如果問題只出現在 WebSocket / 即時聊天 / room 廣播，先看這層
- 如果訊息實際怎麼寫進資料庫或做權限驗證，通常還是要回看 `services/` 或 `blueprints/`
