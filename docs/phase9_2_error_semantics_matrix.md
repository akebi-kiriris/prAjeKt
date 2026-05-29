# Phase 9.2 Error Semantics Matrix（草案）

> 你問的 `error_code -> retryable -> route` 矩陣，就是「同一種錯誤，agent 應該怎麼走下一步」的對照表。  
> 用途：讓 LangGraph 不靠猜測，而是按規則路由到 `retry / ask_user / stop`。

---

## 欄位定義

- `error_code`：機器可判斷錯誤碼
- `retryable`：是否建議自動重試
- `route`：LangGraph 建議路由
- `agent_hint`：給 agent 的下一步指引
- `example_source`：目前專案常見來源

---

## 矩陣（第一版）

| error_code | retryable | route | agent_hint | example_source |
|---|---|---|---|---|
| `VALIDATION_ERROR` | false | `ask_user` | 請補齊必填欄位或修正格式 | payload 驗證失敗 |
| `PERMISSION_DENIED` | false | `stop` | 你目前沒有此操作權限 | 成員/擁有者檢查失敗 |
| `NOT_FOUND` | false | `ask_user` | 請確認資源是否存在或 id 是否正確 | 任務/專案/群組不存在 |
| `CONFLICT` | false | `ask_user` | 資源狀態衝突，請調整參數後重試 | 重複成員、唯一鍵衝突 |
| `UPSTREAM_TIMEOUT` | true | `retry` | 外部服務逾時，稍後重試 | AI 服務 timeout |
| `UPSTREAM_UNAVAILABLE` | true | `retry` | 外部服務暫不可用，請稍後再試 | AI provider 初始化/連線失敗 |
| `INTERNAL_ERROR` | false | `stop` | 系統發生未預期錯誤，請稍後再試 | 未分類例外 |

---

## HTTP 狀態碼映射建議（從現況 `OperationError(status_code)` 過渡）

| status_code | error_code（預設） |
|---|---|
| `400` | `VALIDATION_ERROR` |
| `401` | `AUTHENTICATION_REQUIRED` |
| `403` | `PERMISSION_DENIED` |
| `404` | `NOT_FOUND` |
| `409` | `CONFLICT` |
| `422` | `VALIDATION_ERROR` |
| `429` | `RATE_LIMITED` |
| `500` | `INTERNAL_ERROR` |
| `502` | `UPSTREAM_UNAVAILABLE` |
| `503` | `UPSTREAM_UNAVAILABLE` |
| `504` | `UPSTREAM_TIMEOUT` |

> 備註：9.3 在 tool registry 層集中做 mapping，service 層先不強制改拋錯介面。

---

## 路由規則（LangGraph）

1. `retryable=true`：進 `retry node`（可加退避與次數上限）。
2. `VALIDATION_ERROR / NOT_FOUND / CONFLICT`：進 `ask_user_clarify node`。
3. `PERMISSION_DENIED / INTERNAL_ERROR`：進 `stop_and_explain node`。

---

## 9.3 前置備註

目前多數 service 還是 `OperationError(message, status_code)`，9.3 要做的是：

1. 將 service error 映射到上述 `error_code`。
2. 統一輸出 `ToolError` 格式（含 `retryable` 與 `hint`）。
3. 在 tool registry 層集中做 mapping，避免散落各 service。
