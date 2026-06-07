# backend/services/tools

這層是 agent tool 的執行入口，不直接承載核心商業邏輯，而是把既有 service 包裝成 agent 可安全呼叫的工具。

## 主要檔案

- `registry.py`: 工具定義、查找與統一執行入口
- `handlers.py`: 已驗證輸入進入後，呼叫 service 並包裝結果
- `error_mapper.py`: 將 service / validation 例外轉成標準 tool error

## 執行關係

`registry -> handler -> service`

## 各層責任

- `registry`
  - 保存工具定義
  - 驗證 payload
  - 找到對應 handler
- `handler`
  - 接收已驗證的 input model
  - 呼叫實際 service
  - 轉成標準 success / failure envelope
- `error_mapper`
  - 收斂錯誤語意
  - 提供 agent 路由可讀的錯誤資訊

## 不應該放什麼

- 大量商業邏輯：應回到 `backend/services/` 既有 service
- HTTP request parsing
- 前端專用格式轉換

## 修改判斷

- 新增一個 agent 可呼叫能力時，通常要同時看：
  - `contracts/tool_inputs.py`
  - `contracts/tool_outputs.py`
  - `tools/handlers.py`
  - `tools/registry.py`
- 如果只是修正工具錯誤如何映射成 `VALIDATION_ERROR` / `CONFLICT` 等，改 `error_mapper.py`
