# Backend Services 目錄說明

`backend/services/` 是後端業務流程的核心層，負責協調 repository、執行 domain 規則、串接外部能力，並維持服務層的穩定行為邊界。

## 內容分工

1. `contracts/`
   - 已搬遷至 `backend/contracts/`，作為 backend 共用契約層。
2. `tools/`
   - 給 agent 使用的工具包裝層與執行入口。
3. `*_service.py`
   - 各 domain 的實際業務流程。
4. `transactions.py`
   - 交易與 session 協調輔助。

## 責任範圍

本目錄應負責以下內容：

1. 任務、專案、群組、知識庫等 domain 流程
2. 多個 repository 或外部服務之間的協調
3. 屬於業務語意的驗證、狀態轉換與流程控制

以下內容不應直接放在此層：

1. HTTP request/response 處理
2. 純資料查詢或持久化細節
3. LangGraph 節點與 graph 編排
4. 前端顯示邏輯或 UI 狀態

## 相鄰目錄邊界

1. API 層參數來源、權限與 HTTP 回應，應放 `backend/blueprints/`
2. 純資料存取與查詢封裝，應放 `backend/repositories/`
3. agent 流程節點與圖結構，應放 `backend/chains/`
4. agent 工具 I/O 邊界問題，優先檢查 `backend/contracts/` 與 `tools/`

## 維護原則

1. service 應以業務流程為中心，不重複包裝 route 或 repository 的責任。
2. 若某段邏輯主要是資料契約，應抽至 `backend/contracts/`。
3. 若某段邏輯主要是 agent 工具入口與錯誤映射，應抽至 `tools/`。
