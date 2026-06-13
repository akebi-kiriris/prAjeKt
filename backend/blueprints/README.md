# Backend Blueprints 目錄說明

`backend/blueprints/` 是後端 HTTP 入口層，負責接收 request、處理路由與權限邊界、呼叫 service，並回傳穩定的 API response。

## 責任範圍

本目錄應負責以下內容：

1. request 解析與參數來源整理
2. route 層級的權限檢查
3. 呼叫對應 service
4. 將例外轉成穩定的 HTTP response

以下內容不應放在本目錄：

1. 深層商業邏輯
2. repository 查詢細節
3. agent graph 內部流程

## 相鄰目錄邊界

1. 若變動的是 HTTP status code、response shape 或 route 邊界，優先檢查本目錄。
2. 若變動的是業務規則與狀態轉換，應回到 `backend/services/`。
3. 若變動的是資料查詢與持久化細節，應回到 `backend/repositories/`。
4. 若變動的是 agent 節點流程，應回到 `backend/chains/`。

## 維護原則

1. blueprint 應保持為 API 邊界層，不直接承擔複雜業務流程。
2. API 層驗證與錯誤轉換應維持一致，避免各 route 自行分散處理。
3. 與使用者或操作者上下文有關的 HTTP 邊界，應在此層維持清楚傳遞。
