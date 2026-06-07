# Phase 9 Agent 系統設計與實作全紀錄

> 日期：2026-06-04  
> 範圍：Phase 9.1、9.2、9.3、9.4、9.5  
> 用途：完整記錄 Phase 9 到目前為止做了什麼、為什麼這樣做、各檔案負責什麼，以及目前系統是如何運作的。

---

## 1. 這份文件要解決什麼問題

Phase 9 到目前為止，已經不是單一改動，而是多個階段逐步堆疊出一套新的 agent 系統。

如果只看其中一個檔案，很容易產生下面這些困惑：

1. 為什麼有 `TOOL_REGISTRY`？
2. 為什麼還需要 `handler`？
3. 為什麼不是直接用 LangChain 的 `@tool`？
4. 為什麼 `agent_nodes.py` 還有關鍵詞規則？
5. plan、execute、replan 到底分別在哪一層處理？
6. 前端 `CopilotDock` 跟後端 LangGraph 的關係是什麼？

這份文件就是拿來一次把這些事情講清楚。

---

## 2. Phase 9 的整體目標

Phase 9 的核心目標，不是單純「加一個 AI 功能」，而是把後端逐步工程化，讓它能安全地變成 agent 的工具層。

可以拆成五個階段理解：

### 9.1 Type Hints

目標：

1. 先把 repository / service / validation 等核心邏輯補上型別資訊。
2. 讓後續工具化與契約化時，不需要在模糊型別上硬猜。

### 9.2 Docstring / 契約導向說明

目標：

1. 不是只補註解，而是把「tool-facing 函式的用途、前置條件、副作用、錯誤語意」寫清楚。
2. 讓後續無論是人、模型、或 registry，都有明確的行為契約可以依附。

### 9.3 Tool Registry + LangGraph 最小閉環

目標：

1. 把部分高價值 service 入口轉成白名單工具。
2. 接到 LangGraph，讓使用者一句自然語言需求能觸發多步工具鏈。

### 9.4 Plan -> Confirm -> Execute

目標：

1. 不再讓 agent 收到需求就直接寫資料。
2. 先產生計畫，給使用者確認，再正式執行。

### 9.5 模型提案式 Plan + Replan 強制模型重提案

目標：

1. 讓 plan 階段不只靠關鍵詞規則。
2. 讓模型讀取工具清單與契約，自行提出工具序列與 payload 草案。
3. 但仍保留 fallback 與安全邊界。

---

## 3. Phase 9 到目前為止的成果

如果用一句話總結目前的狀態：

目前已經完成一套「單體後端版、白名單驅動、雙階段確認、模型提案優先」的 Copilot Agent 初版。

現在它已經具備：

1. 工具白名單與 metadata
2. 工具輸入輸出契約
3. 統一錯誤 envelope
4. LangGraph 最小 ReAct 閉環
5. `plan -> confirm -> execute`
6. `replan`
7. 模型提案式 plan
8. 前端全域入口與 plan 預覽面板

但還尚未具備：

1. 完整工具覆蓋
2. 全面 trace / request_id / benchmark
3. 持久化 plan store
4. 回滾 / saga / undo

---

## 4. 為什麼不直接用 LangChain `@tool`

LangChain 確實有 `@tool`，但目前專案沒有採用它。

### 原因

因為我們不只需要「讓模型能呼叫函式」，而是還需要：

1. 明確工具白名單
2. 自訂 `input_model`
3. 自訂 `handler`
4. 給前端顯示的 `user_visible_label`
5. `requires_confirmation`
6. `side_effect_level`
7. `permission_note`
8. 給 plan 階段用的描述與風險資訊

LangChain 的 `@tool` 更偏向：

- 快速把函式包成工具
- 讓 agent 可直接選擇與呼叫

但我們目前需要的是一個更強控制的工具系統，所以走的是：

- 自訂 `ToolDefinition`
- 自訂 `TOOL_REGISTRY`
- 自訂 `handler`
- 自訂 envelope
- 自訂 plan / confirm / execute 流程

所以目前這套不是 LangChain 內建工具系統，而是：

`LangGraph 作為流程引擎 + 我們自己的 registry-based tool system`

---

## 5. 系統的主要分層

目前整個 agent 系統可以拆成七層：

1. Service 業務層
2. Tool 契約層
3. Handler 層
4. Registry 層
5. Agent 流程層（LangGraph）
6. Plan/Execute 編排層
7. 前端互動層

下面逐層說明。

---

## 6. Service 業務層

這是原本就存在的系統核心，真正做事的是它們。

常見例子：

- `create_task_for_user`
- `update_task_for_member`
- `create_timeline_for_user`
- `batch_create_tasks_for_timeline`
- `check_timeline_task_conflicts`
- `generate_group_snapshot`
- `upload_and_index_knowledge_document`

這些函式的責任是：

1. 處理商業邏輯
2. 讀寫資料庫
3. 呼叫 AI 或外部服務
4. 維護既有 API / service 契約

重要觀念：

service 不是為 agent 而生，它本來就是後端業務層。  
Phase 9 做的是「把其中一部分 service 包成 agent 可安全使用的 tools」。

---

## 7. Tool 契約層

主要檔案：

- `backend/services/contracts/tool_inputs.py`
- `backend/services/contracts/tool_outputs.py`
- `backend/services/contracts/tool_envelopes.py`

這層的目的，是把工具的 I/O 固定下來。

### 7.1 `tool_inputs.py`

負責定義每個工具的輸入 schema，例如：

1. 建立任務需要哪些欄位
2. 更新任務可以改哪些欄位
3. 生成任務草案需要哪些脈絡
4. 知識文件上傳需要哪些欄位

這讓工具輸入不再是任意 `dict[str, Any]`，而是有明確結構。

補充：

1. 這些 input model 不只是拿來提示型別，還會在工具執行前真的拿來驗證 payload。
2. 多數 model 會搭配 `model_config = ConfigDict(extra="forbid")`。
3. 這代表工具只接受明確定義的欄位，多餘欄位會直接被拒絕。

這點很重要，因為在 agent 場景裡，LLM 很容易自行猜測欄位名稱；`extra="forbid"` 可以避免錯誤欄位被默默忽略。

### 7.2 `tool_outputs.py`

負責定義成功時的 `data` 內容。

例如：

1. 建立任務後回 `task_id`
2. 建立專案後回 `timeline_id`
3. 查詢任務時回任務清單
4. 生成任務草案時回任務陣列

### 7.3 `tool_envelopes.py`

負責定義統一外層包裝。

目標是讓所有工具都回相同風格：

成功：

```json
{
  "ok": true,
  "data": { ... }
}
```

失敗：

```json
{
  "ok": false,
  "error": {
    "error_code": "...",
    "message": "...",
    "retryable": false,
    "hint": "..."
  }
}
```

這樣 LangGraph 節點與前端才有固定方式可讀。

---

## 8. Error Mapping 層

主要檔案：

- `backend/services/tools/error_mapper.py`

這層的責任是把原本 service / validation 丟出的各種例外，收斂成 agent 可理解的錯誤語意。

### 8.1 `map_exception_to_tool_error`

它做的事：

1. 接收例外
2. 根據 `status_code` 或 `ValidationError`
3. 轉成統一的 `ToolError`

例如：

- `400/422` -> `VALIDATION_ERROR`
- `403` -> `PERMISSION_DENIED`
- `404` -> `NOT_FOUND`
- `409` -> `CONFLICT`
- `504` -> `UPSTREAM_TIMEOUT`

### 8.2 `route_from_tool_error`

這個函式是 LangGraph 路由的重要依據。

它決定：

1. 是否可 retry
2. 是 ask_user 還是 stop

目前策略大致是：

- `retryable=true` -> `retry`
- `VALIDATION_ERROR / NOT_FOUND / CONFLICT` -> `ask_user`
- 其他 -> `stop`

所以 `error_mapper.py` 是工具錯誤與 agent 路由之間的橋樑。

---

## 9. Handler 層

主要檔案：

- `backend/services/tools/handlers.py`

這層很重要，也是最容易讓人混淆的一層。

### 9.1 handler 不是什麼

handler 不是：

1. LangChain 內建工具
2. 真正的核心商業邏輯
3. 主要的資料層

### 9.2 handler 是什麼

handler 是「tool 的入口包裝層」。

它的責任是：

1. 接收 registry 傳進來的「已驗證輸入」
2. 呼叫真正的 service function
3. 用 `tool_outputs.py` 包出成功輸出
4. 用 `error_mapper.py` 把錯誤包成標準 envelope

### 9.3 handler 實際作用

例如 `handle_create_task_for_user`：

1. 接收已驗證的 `CreateTaskToolInput`
2. `create_task_for_user(...)`
3. `TaskCreateToolOutput(...)`
4. `make_success(...)`
5. 失敗時 `make_failure(map_exception_to_tool_error(exc))`

這表示 handler 發揮作用的位置是在：

`registry -> handler -> service`

它不是在前端，也不是在 LangGraph node 內部直接做業務邏輯，而是在「工具執行入口」這一層負責安檢與包裝。

### 9.4 為什麼不能 registry 直接呼叫 service

如果 registry 直接叫 service，會少掉：

1. 統一的 tool-facing 入口
2. 統一成功/失敗包裝
3. 錯誤映射
4. 給 agent 讀取的穩定 envelope

所以 handler 的存在是合理且必要的。

### 9.4 registry 與 handler 的責任分工（收斂後）

經過後續收斂，目前這兩層的責任更明確：

1. registry
   - 保存 `input_model`
   - 統一執行 `input_model.model_validate(payload)`
   - 找出對應 handler

2. handler
   - 不再自己重複 `model_validate(...)`
   - 只接收「已驗證過的 input model」
   - 專心呼叫 service 與包裝結果

這樣可以避免同一份 payload 在 registry 與 handler 內重複驗證兩次。

---

## 10. Registry 層

主要檔案：

- `backend/services/tools/registry.py`

### 10.1 `ToolDefinition` 是什麼

`ToolDefinition` 是我們自己做的，不是框架內建型別。

它是一個 `@dataclass(frozen=True)`，用來描述一個工具。

目前欄位包括：

1. `name`
2. `description`
3. `input_model`
4. `handler`
5. `side_effects`
6. `side_effect_level`
7. `user_visible_label`
8. `requires_confirmation`
9. `permission_note`

它可以理解成一個「工具定義物件」：

1. 描述這個工具叫什麼
2. 描述這個工具吃什麼輸入
3. 描述這個工具要交給誰執行
4. 描述這個工具對模型與前端來說該怎麼理解

### 10.2 `TOOL_REGISTRY` 是什麼

`TOOL_REGISTRY` 是整個 agent 工具白名單。

可以把它理解成：

- agent 可用工具總表
- 模型可見的工具來源
- registry 執行時查找 handler 的索引表

現在所有工具都是在這裡註冊。

所以如果某個 service 函式沒有被包成 handler 並註冊進 `TOOL_REGISTRY`，agent 就不會使用它。

### 10.3 註冊工具時為什麼要帶 `handler`

因為 registry 不是只要知道「有這個工具」，還要知道：

1. 這個工具用哪個 schema 驗證
2. 這個工具實際由哪個入口函式處理

所以工具註冊時一定會綁：

- `input_model`
- `handler`

其中：

1. `input_model`
   - 定義輸入契約
   - 提供 schema 給模型與前端
   - 由 registry 統一做實際驗證

2. `handler`
   - 作為執行入口
   - 負責呼叫 service 並包裝結果

這樣之後 `execute_registered_tool(tool_name, payload)` 才能：

1. 找到對應工具
2. 呼叫對應 handler

### 10.4 `list_registered_tools()`

這是給模型與前端看的工具清單來源。

它會輸出每個工具的：

1. `name`
2. `description`
3. `side_effects`
4. `side_effect_level`
5. `user_visible_label`
6. `requires_confirmation`
7. `permission_note`
8. `input_schema`

### 10.5 `execute_registered_tool()`

這是給 agent 執行工具時的統一入口。

它做的事：

1. 根據 `tool_name` 從 `TOOL_REGISTRY` 找定義
2. 找不到就直接回 `NOT_FOUND`
3. 用該工具的 `input_model` 對 payload 做統一驗證
4. 驗證失敗時直接包成標準錯誤 envelope
5. 驗證成功後呼叫對應 `handler(validated_payload)`

所以 registry 層的核心作用有兩個：

1. 提供工具清單
2. 提供工具執行入口

更精確一點說，現在 registry 同時也是工具層的統一驗證入口。

---

## 11. Agent 流程層（LangGraph）

主要檔案：

- `backend/chains/agent_state.py`
- `backend/chains/agent_nodes.py`
- `backend/chains/agent_graph.py`

### 11.1 `agent_state.py`

定義整個 agent 的狀態模型。

目前主要欄位：

1. `user_message`
2. `context`
3. `tool_payloads`
4. `pending_tools`
5. `executed_tools`
6. `steps`
7. `last_result`
8. `last_error`
9. `route`
10. `ask_user_message`
11. `final_answer`
12. `retry_count`
13. `loop_count`
14. `max_loops`
15. `requires_write`
16. `unsupported_goal`
17. `created_timeline_id`

這些欄位讓 agent 可以跨節點共享執行上下文。

#### `AgentState` 欄位讀寫表

| 欄位 | 主要用途 | 何時寫入 / 更新 | 誰會讀取 |
| --- | --- | --- | --- |
| `user_message` | 保留使用者原始自然語言需求 | `run_react_agent()` 建立 `init_state` 時寫入 | `_build_payload()`、`intent_parse_node()`、`finalize_node()` |
| `context` | 保存 route / user / timeline / task / group 等上下文 | `run_react_agent()` 建立 `init_state` 時寫入 | `_build_payload()` 用來補齊受保護欄位與系統上下文 |
| `tool_payloads` | 保存 plan 階段核准的 payload 草稿或前端補充參數 | `run_react_agent()` 建立 `init_state` 時寫入 | `_build_payload()` 取出對應 tool 的 payload 基底 |
| `pending_tools` | 保存尚未執行的工具順序清單 | `intent_parse_node()` 初始化；`tool_execute_node()` 每執行一步後移除當前工具並回寫 | `tool_select_node()` 判斷是否還要繼續；`tool_execute_node()` 取出下一個 tool |
| `executed_tools` | 保存已執行工具名稱順序 | `run_react_agent()` 先初始化空陣列；`tool_execute_node()` 每成功或失敗執行後 append 回寫 | `run_react_agent()` 回傳結果；前端結果面板與差異檢查會使用 |
| `steps` | 保存每一步的 `tool_name / input / output` | `run_react_agent()` 初始化空陣列；`tool_execute_node()` 每一步執行後 append | `_extract_generated_tasks_from_state()`、`finalize_node()`、前端步驟結果顯示 |
| `last_result` | 保存最近一次成功工具結果 | `tool_execute_node()` 在 `result.ok = true` 時回寫 | 目前主要供除錯與未來擴充；必要時可供後續 node 觀察最近成功輸出 |
| `last_error` | 保存最近一次失敗工具錯誤 envelope | `tool_execute_node()` 在 `result.ok = false` 時回寫；成功時會清空為 `{}` | `route_by_error_node()` 依 `error_code/retryable` 決定路由 |
| `route` | 保存 graph 目前應走的控制路由 | `intent_parse_node()`、`tool_select_node()`、`tool_execute_node()`、`route_by_error_node()`、`agent_graph.py` 的 conditional edge 持續依此流轉 | `_after_select()`、`_after_route()`、`finalize_node()` |
| `ask_user_message` | 保存需要中止或請使用者補資訊時的提示文案 | `intent_parse_node()`、`tool_select_node()`、`route_by_error_node()` 在 `stop/ask_user` 情境下寫入 | `finalize_node()` 產生最終回答時讀取 |
| `final_answer` | 保存最後要回給前端/使用者的總結文字 | `finalize_node()` 產生；`run_react_agent()` 讀取 compile 後結果回傳 | `execute_copilot_agent_request()`、前端 Copilot 結果區 |
| `retry_count` | 保存目前錯誤重試次數 | `run_react_agent()` 初始化為 `0`；`tool_execute_node()` 成功時歸零；`route_by_error_node()` 選擇 retry 時遞增 | `route_by_error_node()` 決定是否超過 retry limit |
| `loop_count` | 保存目前已執行幾輪 select/execute 迴圈 | `run_react_agent()` 初始化為 `0`；`tool_execute_node()` 每次執行後 `+1` | `tool_select_node()` 判斷是否超過 `max_loops` |
| `max_loops` | 保存單次 agent 允許的最大執行步數 | `run_react_agent()` 建立 `init_state` 時寫入 | `tool_select_node()` 讀取並做超步數保護 |
| `requires_write` | 標記此需求是否屬於寫入型操作 | `intent_parse_node()` 透過 `_requires_write_operation()` 推斷後寫入 | `finalize_node()` 決定要回「已完成寫入」或「目前只完成查詢」 |
| `unsupported_goal` | 標記此需求是否超出目前白名單能力 | `intent_parse_node()` 透過 `_is_unsupported_goal()` 推斷後寫入 | `finalize_node()` 產生更明確的「目前未支援此目標」回答 |
| `created_timeline_id` | 暫存執行過程中新建立的專案 ID，供後續工具串接 | `tool_execute_node()` 在 `create_timeline_for_user` 成功後從 result/data 或 payload 擷取並回寫 | `_build_payload()` 用來自動補後續工具的 `timeline_id` |

補一句最重要的觀念：

這份 state 不是單純的暫存 dict，而是目前整張 LangGraph 的共享工作記憶。  
工具之間不是彼此直接呼叫，而是透過「前一步寫 state、下一步再讀 state」的方式串接。

### 11.2 `agent_nodes.py`

這支是目前實際執行流程最核心的檔案。

#### 關鍵 helper

1. `_sanitize_user_payload`
   - 移除不可覆寫欄位

2. `_build_payload`
   - 根據當前 tool 與 state 組出要送進 handler 的 payload

3. `build_pending_tools`
   - 規則式工具序列產生器
   - 目前仍存在，但在 9.5 之後定位已降為 fallback / 保底層

#### 核心 nodes

1. `intent_parse_node`
   - 判斷需求是否支援
   - 決定初始 `pending_tools`

2. `tool_select_node`
   - 判斷下一步該繼續還是 finalize / stop

3. `tool_execute_node`
   - 取出下一個工具
   - 建 payload
   - 呼叫 `execute_registered_tool`
   - 將步驟結果寫進 `steps`

4. `route_by_error_node`
   - 依 `last_error` 決定 retry / ask_user / stop

5. `finalize_node`
   - 根據整體 state 產出最後給使用者的訊息

### 11.3 `agent_graph.py`

這是 LangGraph 的接線檔。

目前流程是：

1. `intent_parse`
2. `select`
3. `execute`
4. `route_error`
5. `finalize`

這就是目前 agent 的最小閉環。

要特別注意：

這張 graph 是「固定執行圖」，不是「每個業務工具各自一個 node 的流程圖」。

也就是說，現在不是畫成：

`create_timeline -> generate_tasks -> batch_create`

而是畫成：

`intent_parse -> select -> execute_current_tool -> route_error -> ...`

真正的工具順序存在 `pending_tools` 裡，不存在 edges 上。

### 11.4 `run_react_agent()` 與 `create_agent_graph()` 的關係

目前真正啟動 LangGraph 的入口是在 `agent_graph.py` 的：

1. `create_agent_graph()`
2. `run_react_agent()`

兩者分工如下：

#### `create_agent_graph()`

負責把整張 graph 建好並 compile：

1. 宣告有哪些 nodes
2. 宣告 entry point
3. 宣告一般 edge
4. 宣告 conditional edge

也就是說，它負責建立整個執行流程骨架。

#### `run_react_agent()`

負責：

1. 建立 `init_state`
2. 將 `pending_tools`、`context`、`tool_payloads` 放進 state
3. 呼叫 compile 後的 graph：`app.invoke(init_state)`

所以可以把這個關係記成：

`create_agent_graph()` = 先把流程圖建好  
`run_react_agent()` = 把初始 state 放進去，正式執行這張流程圖

### 11.5 conditional edge 在這裡到底做了什麼

目前最關鍵的 conditional edge 之一是：

```python
graph.add_conditional_edges(
    "select",
    _after_select,
    {"execute": "execute", "finalize": "finalize"},
)
```

這段不是在決定「下一個業務工具是哪個」，而是在決定：

1. 還要不要再執行下一步工具
2. 還是流程已經可以收尾

它的判斷依據不是直接看工具名稱，而是看 state 裡目前的狀態，例如：

1. `pending_tools` 是否還有剩
2. `route` 是否已經被標成 `finalize`
3. `route` 是否已經被標成 `stop`

所以它的角色比較像：

`流程控制器`

不是：

`業務工具排序器`

### 11.6 多個工具為什麼會在同一個 node 裡反覆執行

這是因為現在的 graph 設計是：

1. 工具順序放在 state 的 `pending_tools`
2. `tool_execute_node()` 每次只執行一個工具
3. 執行完後再透過 edge 回到 `select`
4. `select` 判斷是否還要再進下一輪 `execute`

所以多工具執行的本質是：

`同一個 execute node + 多輪 state 推進`

不是：

`每個工具一個獨立 node`

### 11.7 工具執行後的結果放在哪裡

每次工具執行完後，結果會被寫回 state，主要欄位包括：

1. `steps`
   - 紀錄每一步：
     - `tool_name`
     - `input`
     - `output`

2. `executed_tools`
   - 紀錄已執行的工具名稱順序

3. `last_result`
   - 最近一次成功結果

4. `last_error`
   - 最近一次失敗錯誤

5. 特定衍生欄位
   - 例如 `created_timeline_id`
   - 讓後續工具可接續使用前一步產生的資源

也就是說，工具不是互相直接呼叫，而是：

`前一步結果先寫回 state -> 下一步再從 state 讀出需要的資料`

### 11.4 目前為什麼還有關鍵詞規則

你之前問過這點，這裡正式記錄下來。

`build_pending_tools()` 目前還存在，原因是：

1. 9.3 一開始本來就是規則式選工具
2. 9.5 只把 plan 階段升級成模型提案優先
3. 直接跑 `run_react_agent()` 且沒帶 `pending_tools` 時，`intent_parse_node()` 仍會用它補一份工具序列

所以目前狀態不是「還是主要靠關鍵詞」，而是：

- `plan`：模型提案優先
- `replan`：強制模型提案
- `agent_nodes.py`：仍保留關鍵詞 fallback / 保底邏輯

這是半切換，不是完全拔除。

### 11.5 現在到底算不算典型 ReAct

嚴格來說，目前正式主線已經比較接近：

`plan-and-execute agent`

而不是典型的自由式 ReAct。

原因是：

1. `plan` 階段通常已先產生完整 `pending_tools`
2. 使用者確認後才執行
3. execute 階段主要是照已核准步驟執行
4. LangGraph 負責的是執行期 state、payload 串接與錯誤路由

所以比較準確的說法是：

1. 9.3 初版有較濃的簡化 ReAct 味道
2. 9.4 / 9.5 正式主線是「模型提案 + 使用者確認 + LangGraph 執行」

---

## 12. Plan / Execute 編排層

主要檔案：

- `backend/services/copilot_service.py`
- `backend/services/agent_plan_service.py`
- `backend/services/tool_plan_service.py`

### 12.1 `copilot_service.py`

這支是整個 Copilot agent 的應用層總編排器。

它同時承擔三條路線：

1. 舊 MCP 路線
2. Agent plan / reject / execute 路線
3. 9.5 模型提案式 plan 路線

#### MCP 路線

`execute_copilot_mcp_request()`

這是舊有自然語言 -> MCP 工具執行流程，仍保留相容。

#### Agent 路線

1. `create_copilot_agent_plan()`
2. `reject_copilot_agent_plan()`
3. `execute_copilot_agent_plan()`
4. `execute_copilot_agent_request()`

#### 9.5 升級內容

1. `_propose_pending_tools()`
   - LLM proposal 優先
   - 失敗才 fallback `build_pending_tools`

2. `_merge_tool_payloads()`
   - 合併前端輸入與模型草稿 payload
   - 同時清理敏感欄位

3. `_serialize_plan()`
   - 現在會回 `proposal_source` / `proposal_reason`

這代表 `copilot_service.py` 其實是整個 agent 系統的高層 orchestration service：

1. plan 怎麼產生
2. plan 怎麼存
3. execute 只能讀哪一份快照
4. replan 是否必須強制模型重提案
5. 最後怎麼把資料交給 LangGraph 執行

### 12.2 `agent_plan_service.py`

這是 9.4 新增的 plan store。

它目前是 in-memory，負責管理：

1. `plan_id`
2. `status`
3. `goal`
4. `context`
5. `approved_tool_payloads`
6. `pending_tools`
7. `summary`
8. `steps_preview`
9. `risk_notes`
10. `proposal_source`
11. `proposal_reason`
12. `execution_id`
13. `expires_at`

它也提供狀態流轉：

1. `create_plan`
2. `get_plan`
3. `reject_plan`
4. `mark_executing`
5. `mark_executed`

### 12.3 `tool_plan_service.py`

這是 9.5 新增的模型提案服務。

它的責任不是執行工具，而是：

1. 把工具清單轉成模型可讀 prompt
2. 要求模型輸出固定 JSON proposal
3. 解析 JSON
4. 驗證 proposal 是否只使用白名單工具
5. 取出 `steps / payload_draft / reason`

它的輸出契約目前是：

```json
{
  "supported": true,
  "steps": ["tool_a", "tool_b"],
  "payload_draft": {"tool_a": {"key": "value"}},
  "reason": "..."
}
```

---

## 13. API 層

主要檔案：

- `backend/blueprints/copilot.py`

這支 blueprint 把前端與編排層接起來。

目前主要 API：

1. `POST /api/copilot/mcp/execute`
2. `GET /api/copilot/agent/tools`
3. `POST /api/copilot/agent/plan`
4. `POST /api/copilot/agent/execute`
5. `POST /api/copilot/agent/reject`
6. `POST /api/copilot/agent/replan`

### 各 API 的角色

#### `/agent/tools`

回傳目前 registry 已開放的工具清單。

#### `/agent/plan`

只規劃，不執行。

#### `/agent/execute`

只執行已確認的 `plan_id`。

#### `/agent/reject`

拒絕既有 plan。

#### `/agent/replan`

先拒絕舊 plan，再強制模型重提案，產生新 `plan_id`。

---

## 14. 前端層

主要檔案：

- `frontend/src/components/CopilotDock.vue`
- `frontend/src/services/copilotService.ts`
- `frontend/src/types/copilot.ts`

### 14.1 `CopilotDock.vue`

這是目前使用者真正看到的 agent 入口。

功能分成三段：

1. 自然語言輸入
2. plan 預覽
3. execute 結果

它的重點設計是：

1. 使用者不手填工具參數
2. context 由系統自動帶入
3. 先顯示 plan，再確認執行
4. 可在前端做 replan
5. 顯示提案來源與提案說明

### 14.2 `copilotService.ts`

負責呼叫後端：

1. create plan
2. execute plan
3. reject plan
4. replan

### 14.3 `copilot.ts`

定義前端對應的型別契約，例如：

1. `CopilotAgentPlanResponse`
2. `CopilotAgentExecuteResponse`
3. `CopilotAgentStep`

這讓 plan / execute 回傳格式在前端也保持穩定。

---

## 15. 從使用者輸入到 service 執行的完整路徑

這裡用最完整的路徑說一次。

### 15.1 Plan 階段

1. 使用者在 `CopilotDock.vue` 輸入自然語言目標
2. 前端呼叫 `POST /api/copilot/agent/plan`
3. `copilot.py` 進入 `create_copilot_agent_plan()`
4. `copilot_service.py` 呼叫 `_propose_pending_tools()`
5. `_propose_pending_tools()`：
   - 讀取 `list_registered_tools()`
   - 呼叫 `propose_plan_with_llm()`
   - 成功則取得 `steps + payload_draft + reason`
   - 失敗則 fallback `build_pending_tools()`
6. `copilot_service.py` 建立 `AgentPlanRecord`
7. 回傳：
   - `summary`
   - `steps_preview`
   - `risk_notes`
   - `proposal_source`
   - `proposal_reason`

### 15.2 Execute 階段

1. 使用者按確認執行
2. 前端呼叫 `POST /api/copilot/agent/execute`
3. `copilot.py` 進入 `execute_copilot_agent_plan()`
4. 後端讀取已核准 `plan_id`
5. 檢查：
   - `confirm`
   - `status`
   - execute 階段不可覆寫 `tool_payloads`
6. 呼叫 `execute_copilot_agent_request()`
7. 進入 `run_react_agent()`
8. LangGraph 開始跑 nodes
9. `tool_execute_node()` 取出下一個 tool
10. `_build_payload()` 產生執行 payload
11. `execute_registered_tool(tool_name, payload)`
12. registry 根據 `tool_name` 找到 `handler`
13. `handler`：
   - 接收已驗證輸入
   - 呼叫 service
   - 包 success/failure envelope
14. 結果回到 LangGraph state
15. 依錯誤語意決定 continue / ask_user / stop / finalize
16. 全部結束後，回傳 `steps`、`executed_tools`、`final_answer`

補一句最重要的理解：

多個函數的執行順序，不是靠很多業務 nodes / edges 事先畫出來，而是：

1. plan 階段先把工具序列放進 `pending_tools`
2. execute 階段由固定 graph 一輪一輪拿 `pending_tools[0]` 出來執行

所以目前是：

`固定 graph + 動態工具序列`

而不是：

`固定工具圖 + 動態走邊`

---

## 16. 各角色一句話版本

如果要用最短句子記住：

### `ToolDefinition`

描述一個工具的 metadata 與執行入口。

### `TOOL_REGISTRY`

整個 agent 可用工具的白名單總表。

### `handler`

工具入口包裝層，負責驗證、轉接、包裝結果。

### `service`

真正執行業務邏輯的地方。

### `registry`

決定某個工具名稱對應哪個 handler。

### `agent_nodes`

決定整個 agent 每一步要做什麼。

### `agent_graph`

把各節點接成 LangGraph 流程。

### `copilot_service`

負責 plan / execute / replan 的高層編排。

### `agent_plan_service`

保存 plan snapshot 與狀態流轉。

### `tool_plan_service`

讓模型根據工具清單提出 steps 與 payload 草案。

### `CopilotDock`

使用者操作 agent 的前端入口。

---

## 17. Phase 9.3、9.4、9.5 分別實際改變了什麼

### 17.1 9.3 的改變

從：

- service 只能被後端 API 或內部程式直接呼叫

變成：

- 有一層 registry + handler + schema 的 tool 系統
- 並接到 LangGraph

### 17.2 9.4 的改變

從：

- 輸入一句話就直接執行

變成：

- 先產生計畫
- 再使用者確認
- 再正式執行

### 17.3 9.5 的改變

從：

- 主要靠 `build_pending_tools()` 關鍵詞規則產生步驟

變成：

- 先由模型讀工具清單提出 plan
- plan 失敗才 fallback 規則
- replan 強制重跑模型提案

---

## 18. 目前的安全邊界

目前已建立的安全邊界包括：

1. 工具白名單
   - 只有 `TOOL_REGISTRY` 內註冊的工具可用

2. 敏感欄位清洗
   - `user_id`
   - `actor_user_id`
   - `created_by`
   - `timeline_id`
   - `task_id`
   - `group_id`

3. 統一 schema 驗證
   - 所有 handler 都先走 `model_validate`

4. 統一錯誤 envelope
   - `error_code`
   - `retryable`
   - `hint`

5. 使用者確認後才寫入
   - `plan -> confirm -> execute`

6. execute 階段不可覆寫已核准參數

7. replan 必須重新提案與重新確認

---

## 19. 目前仍未完成的部分

這部分很重要，避免高估現況。

目前仍未完成：

1. 全 service 工具化
   - 目前只有第一批高價值入口完成

2. 完整移除關鍵詞規則
   - `build_pending_tools()` 仍存在，現在是 fallback / 保底邏輯

3. Plan store 持久化
   - 目前是 in-memory

4. 完整可觀測性
   - 尚未有 request_id / trace hook / benchmark

5. 補償回滾
   - 目前採「先確認，再執行」策略，尚未做 undo

6. 全面高品質模型規劃
   - 9.5 已經有 proposal，但整體仍是第一版

---

## 20. Phase 9 到目前為止的實際定位

如果要很務實地定義目前系統，不要說成「完整 agent 平台」，比較精準的說法是：

目前已完成一個：

1. 單體後端版
2. 白名單驅動
3. 契約化工具層
4. LangGraph 最小閉環
5. 使用者確認後才執行
6. 模型提案優先的 Copilot Agent 初版

---

## 21. 為什麼 9.6 會是下一步

因為 9.3、9.4、9.5 已經把流程骨架搭好了：

1. 有工具
2. 有 plan
3. 有 execute
4. 有 proposal source
5. 有 proposal reason
6. 有步驟結果

下一步自然就是問：

1. 成功率多少？
2. 哪些路由最常失敗？
3. 哪些工具容易出錯？
4. replan 有沒有真的改善結果？
5. plan 與 execute 哪裡耗時？

所以 9.6 的任務才會是：

1. trace
2. request_id
3. benchmark 題集
4. benchmark runner
5. 報表

也就是把現在這套 agent 變得「可量測、可比較、可持續調整」。

---

## 22. 最後總結

Phase 9 到目前為止，最本質的變化不是多了一個 AI 面板，而是系統的後端已經開始從：

`一組 service 函式`

逐步演化成：

`一組有契約、有白名單、有確認機制、有規劃流程的 agent 工具系統`

這也是為什麼目前你會覺得改動很多。  
因為這不是單一功能，而是在替後續 agent 能穩定擴充，先打地基。
