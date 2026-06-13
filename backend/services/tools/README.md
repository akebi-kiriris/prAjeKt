# Backend Service Tools 目錄說明

`backend/services/tools/` 是 agent tool 的執行入口，負責把既有後端能力包裝成可安全呼叫的工具介面。這層的重點是工具註冊、schema 對接、handler 執行與錯誤語意收斂，而不是重新承擔核心商業邏輯。

## 內容範圍

本目錄主要包含以下角色：

1. `registry`
   - 工具定義、查找、schema 掛接與統一執行入口。
2. `handlers`
   - 接收已驗證 input，呼叫對應 service，並回傳標準 envelope。
3. `error_mapper`
   - 將 validation、service 或 domain 例外收斂成穩定錯誤碼與訊息。

## 責任邊界

本目錄應負責：

1. agent 可呼叫能力的封裝
2. input/output 契約與 handler 的銜接
3. 工具 metadata 與執行入口統一
4. 錯誤語意與回傳格式收斂

以下內容不應直接放在本目錄：

1. 大量商業邏輯
2. 資料庫查詢細節
3. HTTP request parsing
4. 前端專用的展示格式轉換

## 相鄰目錄邊界

1. `contracts/` 定義工具可接受與可回傳的資料外型。
2. `services/` 負責真正的 domain 流程與資料操作。
3. `chains/` 負責 agent 節點順序、流程分支與 graph 控制。

## 維護原則

1. handler 應保持輕量，不重複實作 service 已有邏輯。
2. 工具回傳格式若有變動，應同步檢查契約、consumer 與測試。
3. 若問題屬於商業規則而非工具入口，應優先回到 `backend/services/`。
