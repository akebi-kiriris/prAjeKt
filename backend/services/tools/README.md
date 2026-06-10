# backend/services/tools

這層是 agent tool 的執行入口，負責把既有後端能力包裝成 agent 可安全呼叫的工具，但不應直接承擔核心商業邏輯。

可以把它理解成：

- `contracts/` 定義輸入輸出長什麼樣
- `tools/` 負責把這些契約接起來並執行
- `services/` 才是實際做事的地方

## 主要檔案

- `registry.py`
  - 工具定義、查找、輸入驗證與統一執行入口
- `handlers.py`
  - 接收已驗證 input，呼叫 service，回傳標準 envelope
- `error_mapper.py`
  - 將 validation / service / domain 例外收斂成標準 tool error

## 執行關係

`registry -> handler -> service`

## 最重要的責任分界

### registry 負責

- 工具是否有註冊
- payload 該用哪個 input schema 驗證
- 執行時要呼叫哪個 handler
- 最外層執行入口是否一致

### handler 負責

- 接收已驗證的 input model
- 呼叫對應 service
- 把 service 回傳包成標準 success envelope
- 捕捉並交給 error mapper 處理錯誤

### error mapper 負責

- 把例外分類成穩定錯誤碼
- 產出 agent 與前端可判讀的錯誤訊息

### service 負責

- 真正的商業邏輯
- 資料查詢 / 寫入
- domain 狀態轉換

一句話版本：

- `tools/` 是 agent 與既有後端能力之間的安全轉接層

## 這層應該負責什麼

- agent 可呼叫能力的封裝
- schema 驗證與 handler 對接
- 工具 metadata 與執行入口統一
- 錯誤語意收斂

## 這層不應該放什麼

- 大量商業邏輯
- 重新實作一份 service 流程
- HTTP request parsing
- 前端專用格式轉換
- 資料庫查詢細節

## registry / handler / service 怎麼切

### 該留在 registry 的內容

- 工具名稱
- 描述與 metadata
- input / output schema 掛接
- 執行入口分派

### 該留在 handler 的內容

- 把 schema model 轉進 service 呼叫
- 少量 orchestration
- 包 success / failure envelope

### 不該塞進 handler 的內容

- 長篇商業規則
- 與 agent 無關的 domain 狀態轉移
- 重複實作 service 已經有的邏輯

如果 handler 越寫越像「另一份 service」，通常就是開始失焦了。

## 新增一個 tool 時的最小檢查表

通常至少會碰到：

- `contracts/tool_inputs.py`
- `contracts/tool_outputs.py`
- `tools/handlers.py`
- `tools/registry.py`
- 必要時 `error_mapper.py`

建議流程：

1. 先定義 input / output 契約
2. 再補 registry metadata
3. 再寫 handler 接既有 service
4. 最後確認錯誤碼是否有對齊

## 常見錯誤訊號

### 代表 registry 可能有問題

- 工具名稱找不到
- schema 沒掛上
- 執行入口分派錯誤

### 代表 handler 可能有問題

- schema 明明過了，但 service 收到錯的欄位
- success envelope shape 不穩定
- 同一種錯誤被包成不同格式

### 代表 error mapper 可能有問題

- 同一種 domain error 有時是 `VALIDATION_ERROR`，有時是 `INTERNAL_ERROR`
- 前端或 agent 無法根據錯誤碼做穩定處理

## 變更時要一起檢查什麼

### 改 registry metadata 時

同步檢查：

- planner / selector 是否依賴這些 metadata
- tool name 是否被 prompt 或測試寫死

### 改 handler 回傳格式時

同步檢查：

- `contracts/tool_outputs.py`
- `contracts/tool_envelopes.py`
- agent node / 前端 consumer

### 改錯誤映射時

同步檢查：

- `error_mapper.py`
- agent fallback 邏輯
- 前端錯誤顯示

## 修改判斷速查

- 新增 agent 可呼叫能力：先看 `registry.py` + `handlers.py` + `contracts/`
- 只是修正工具錯誤如何映射成 `VALIDATION_ERROR` / `CONFLICT` 等：改 `error_mapper.py`
- 如果你正在寫很多 domain 規則，先停一下，通常應該回到 `backend/services/`
