# backend/services/contracts

這層負責定義後端 service 與 agent tool 的資料契約，核心目標是讓 I/O 有明確 schema、欄位限制與錯誤邊界，而不是在各處任意傳 `dict`。

可以把它理解成：

- `services/` 負責真正做事
- `contracts/` 負責說清楚「能收什麼、會回什麼、哪種資料直接拒絕」

## 主要檔案與角色

- `task_contracts.py`
  - 任務相關 request schema、欄位驗證與正規化
- `timeline_contracts.py`
  - timeline / 衝突分析 / 專案相關 schema
- `tool_inputs.py`
  - agent tool 輸入 model
- `tool_outputs.py`
  - agent tool 成功回傳 `data` 的結構
- `tool_envelopes.py`
  - success / failure 外層包裝與標準欄位

## 這層應該負責什麼

- 欄位型別定義
- 必填 / 選填規則
- 格式檢查與正規化
- 拒絕未知欄位
- 跨欄位一致性驗證
- agent tool 的穩定輸入輸出契約

## 這層不應該負責什麼

- 真正的商業邏輯
- repository / database 查詢
- HTTP route 控制
- LangGraph 節點流程
- handler 執行順序

## 最重要的分界

### contracts 層負責

- 這個 payload 合不合法
- 欄位型別對不對
- 某欄位可不可以為空
- 哪些欄位不能讓模型或前端亂塞
- success / error 的外型長怎樣

### services / tools 層負責

- 合法資料進來後要怎麼執行
- 執行失敗要怎麼處理
- 要不要呼叫哪個 service
- 實際資料要怎麼查或寫

一句話版本：

- `contracts/` 負責「資料長什麼樣才算合法」
- `services/` / `tools/` 負責「合法之後怎麼做事」

## 常見契約分層

### domain contracts

例如：

- `task_contracts.py`
- `timeline_contracts.py`

用途：

- 給一般 service 或 route 使用
- 規範 domain request / response 結構

### tool contracts

例如：

- `tool_inputs.py`
- `tool_outputs.py`
- `tool_envelopes.py`

用途：

- 給 agent tools 使用
- 強化模型可呼叫介面的穩定性
- 讓 registry / handler / agent node 都看到一致格式

## 撰寫原則

- 優先使用 Pydantic model 明確定義欄位
- 要拒絕未知欄位時，使用 `ConfigDict(extra="forbid")`
- 單欄位清洗或格式修正可放 field validator
- 跨欄位邏輯檢查可放 model validator
- 型別描述越清楚越好，不要靠註解猜意思

## 什麼該放 validator，什麼不該

### 可以放

- trim 字串
- 空字串轉 `None`
- enum 值合法性
- 日期 / ID / 名稱格式檢查
- 欄位間必要依賴關係

### 不該放

- 查資料庫確認某 ID 是否存在
- 決定目前商業流程是否允許這個操作
- 根據外部服務狀態做條件判斷

如果驗證邏輯需要：

- 查 DB
- 看目前使用者權限狀態
- 依賴多個 service 狀態

那通常代表它已經不是純契約驗證，應回到 service 層。

## tool 契約特別原則

### `tool_inputs.py`

適合放：

- agent 可傳入的欄位
- 模型可控欄位與不可控欄位邊界
- payload 清洗與格式驗證

不適合放：

- 系統注入欄位的商業決策
- handler 執行細節

### `tool_outputs.py`

適合放：

- 成功時 `data` 的固定欄位
- 回傳資料的可依賴 shape

不適合放：

- 錯誤分類
- 執行流程資訊

### `tool_envelopes.py`

適合放：

- 統一 success / error 外層格式
- `ok`, `error_code`, `message`, `data` 等共通欄位

不適合放：

- 特定 domain 的深層商業語意

## 變更契約時要一起檢查什麼

### 改 input schema 時

同步檢查：

- `backend/services/tools/registry.py`
- `backend/services/tools/handlers.py`
- 前端或 agent 是否仍送相同 payload
- 測試是否還符合新欄位規則

### 改 output schema 時

同步檢查：

- 使用該工具結果的 agent node
- 前端 consumer
- parser / envelope 測試

### 改 envelope 時

同步檢查：

- `error_mapper.py`
- agent fallback / confirm / execute 流程
- 前端錯誤顯示與錯誤碼對照

## 修改判斷速查

- 某欄位應不應該接受 `null`：先看這裡
- 想禁止模型傳某些欄位：先看這裡
- 想統一工具回傳的 `data` 結構：先看這裡
- 若只是 service 內部計算流程改變，但對外 schema 不變，通常不用改這裡

## 這層的目標

這層不是為了把所有驗證都塞進 Pydantic，而是為了讓資料邊界變清楚：

- 哪裡在收資料
- 哪裡在拒絕壞資料
- 哪裡可以放心假設資料已合法

只要這層夠穩，後面的 service 與 agent flow 就比較不容易一路傳著模糊 payload 跑下去。
