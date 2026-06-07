# backend/services

這層是後端的業務核心。主要責任是處理商業邏輯、協調 repository、呼叫外部服務，並維持既有 service 契約。

## 目錄分工

- `contracts/`: 輸入輸出 schema 與驗證規則
- `tools/`: 給 agent 使用的工具包裝層
- 其餘 `*_service.py`: 實際業務邏輯
- `transactions.py`: 交易與 session 邊界協調

## 這層應該放什麼

- 任務、專案、群組、知識庫等業務流程
- 多個 repository / 外部服務的協調
- 明確屬於後端 domain 的驗證與狀態轉換

## 不應該放什麼

- HTTP request / response 處理：放到 `backend/blueprints/`
- 純資料存取細節：放到 `backend/repositories/`
- LangGraph 節點流程：放到 `backend/chains/`
- 前端展示或 UI 狀態處理

## Phase 9 相關提醒

- service 不是為 agent 而生；Phase 9 是把既有 service 包成 agent 可安全呼叫的工具。
- 若是 agent tool 的 I/O 邊界問題，優先看 `contracts/` 與 `tools/`，不要把 envelope / payload 組裝直接塞回 service。

## 新增功能時的放置原則

- 如果是「真正做事」的業務流程，先考慮新增或調整 `*_service.py`
- 如果是給 agent 的工具輸入輸出格式，改 `contracts/`
- 如果是 agent 執行工具時的包裝、錯誤映射、註冊，改 `tools/`
