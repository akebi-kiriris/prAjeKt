# Future：Agent 工具 Payload Adapter 與契約映射整理

> 日期：2026-06-29  
> 狀態：future backlog  
> 來源：Agent `generate_timeline_tasks_with_ai` → `batch_create_tasks_for_timeline` 的 step-to-step payload shape 修正

---

## 1. 背景

目前 Copilot Agent 的執行主線由 `backend/chains/agent_nodes.py` 負責：

1. 解析意圖
2. 選擇下一個 tool
3. 組裝 tool payload
4. 執行 tool
5. 將前一步結果帶入下一步
6. 根據錯誤路由 retry / ask_user / stop / finalize

這讓早期 agent flow 可以快速閉環，但也開始出現一個維護訊號：

當某個 tool 的 output 要餵給另一個 tool 的 input 時，兩者不一定共用同一份 payload contract。

例如：

1. `generate_timeline_tasks_with_ai` 產出的 task 是 response / UI shape
2. `batch_create_tasks_for_timeline` 需要的是 batch-create input shape
3. response 會包含 `timeline_id`、`completed` 等欄位
4. batch-create item contract 使用 `extra="forbid"`，不允許這些 response-only 欄位

短期已在 `agent_nodes.py` 補上 narrow normalization，避免 response-only 欄位直接流入下一個 tool。

---

## 2. 名詞釐清

這類邏輯不完全是 validation。

比較精準的拆法：

1. `validation`
   - 檢查 payload 是否符合 contract
   - 例如 Pydantic `extra="forbid"`、必填欄位、型別與值域

2. `normalization`
   - 將資料整理成穩定格式
   - 例如把空字串轉成 `None`、把數字字串轉成 int、移除不該傳遞的欄位

3. `mapping`
   - 將來源 shape 轉成目標 shape
   - 例如 tool A output 轉 tool B input

4. `adapter`
   - 專門負責跨邊界轉換的薄層
   - 在 agent tool 場景中可稱為 `tool payload adapter`

5. `sanitization`
   - 移除不允許或不該由外部提供的欄位
   - 例如 `user_id`、`actor_user_id`、`timeline_id`、`completed` 等不屬於目標 item contract 的欄位

本議題比較適合稱為：

`tool payload adapter / contract mapping`

---

## 3. 目前短期做法

目前短期做法是：

1. 保持 `TimelineBatchCreateTasksToolInput` 嚴格
2. 不放寬 `BatchCreateTaskItem.extra="forbid"`
3. 在 `agent_nodes.py` 內，將 generated task 轉為 batch-create 可接受的 item shape
4. 補測試覆蓋 `timeline_id` / `completed` / unknown field 被移除

這個做法短期可接受，原因：

1. bug 發生在 agent graph 的 step-to-step payload transfer
2. `_build_payload()` 目前本來就是 agent state 到 tool input 的組裝點
3. 當下只有少數跨 step payload 需要 adapter
4. 不急著為單一案例新增一層抽象

---

## 4. 長期風險

如果未來持續把各 tool 的 payload normalization 放在 `agent_nodes.py`，會有幾個問題：

1. `agent_nodes.py` 會從流程節點變成各 tool adapter 的集中地
2. 新增 tool 時容易忘記補對應 mapping
3. tool-specific 知識會散落在 graph flow 內
4. 測試會越來越難分辨是在測 graph flow，還是在測某個 tool 的 payload adapter
5. 多個 tool 若共用類似轉換規則，容易重複實作

`agent_nodes.py` 長期比較適合保留：

1. flow control
2. state transition
3. error routing
4. trace event
5. finalize summary

不適合無限制承載所有 tool 的 payload shape knowledge。

---

## 5. 未來建議方向

### 方向一：新增 tool payload adapter 模組

候選檔案：

1. `backend/services/tools/payload_adapters.py`
2. `backend/services/tools/payload_builders.py`

可能責任：

1. 根據 tool name 與 agent state 建立 payload
2. 將前一步 tool output 轉成下一步 tool input
3. 將 response-only fields 移除
4. 保留目標 contract 允許的欄位

`agent_nodes.py` 可以只呼叫：

```python
payload = build_tool_payload(tool_name=tool_name, state=state)
```

---

### 方向二：讓 registry metadata 掛 payload builder

未來 `ToolDefinition` 可考慮新增：

1. `payload_builder`
2. `output_adapter`
3. `depends_on_output_from`
4. `input_shape_kind`

概念上：

1. registry 知道每個 tool 的 input contract
2. adapter 知道怎麼從 state / prior step result 組 payload
3. graph 只負責照順序呼叫，不知道每個 tool 的細節

---

### 方向三：區分 direct input 與 derived input

Agent tool payload 來源可分成三種：

1. `context`
   - 由後端或頁面提供
   - 例如 `user_id`、`timeline_id`、`task_id`、`group_id`

2. `payload_draft`
   - 由 planner 提案
   - 例如任務名稱、描述、日期、依賴文字

3. `derived_from_steps`
   - 由前面 tool output 推導
   - 例如 AI generated tasks 轉 batch-create tasks

未來 adapter 可明確把三種來源分開，避免資料來源混在 `_build_payload()` 裡。

---

## 6. 何時值得抽出

目前不急著抽。

若出現以下任一情況，再回來整理：

1. 新增 2 到 3 個以上需要跨 step output → input mapping 的 tool
2. `_build_payload()` 再明顯變長
3. tool-specific normalization 開始重複
4. agent graph 測試開始大量關心 payload 細節
5. 新增 tool 時需要修改 `agent_nodes.py` 多個區塊
6. planner / registry / graph 的責任邊界再次變模糊

---

## 7. 不建議的方向

### 1. 不建議放寬 target contract

例如不應為了讓 generated task 可以直接通過，而把 `BatchCreateTaskItem.extra` 改成 allow。

原因：

1. 會讓錯誤欄位被默默吞掉
2. tool input contract 會失去防線
3. 後續模型或 adapter 產生錯欄位時更難被發現

### 2. 不建議讓 planner 承擔所有轉換

Planner 可以提案 payload draft，但不應要求模型完全理解每個 internal response shape 與 target input shape 的差異。

原因：

1. 模型輸出不穩定
2. contract mapping 應由程式保證
3. response-only fields 與 protected fields 不應靠 prompt 約束

### 3. 不建議讓 service layer 接受 agent 專用鬆散格式

Service 應維持業務行為與穩定 input contract。

Agent adapter 應在呼叫 service / tool handler 前完成轉換。

---

## 8. 建議實作順序

### Step 1

維持目前短期修法，只保留針對 generated task → batch-create item 的 narrow normalization。

### Step 2

若新增下一個跨 step mapping，再先觀察是否重複。

### Step 3

當重複或 `_build_payload()` 明顯變胖時，新增 `payload_adapters.py`，先搬出：

1. generated task → batch-create item
2. conflict payload → update task payload
3. update task payload → conflict payload

### Step 4

再評估是否讓 `ToolDefinition` 掛 adapter / builder metadata。

---

## 9. 結論

目前把 generated task normalization 放在 `agent_nodes.py` 是短期合理修正，但不應變成長期模式。

長期方向應該是：

1. `agent_nodes.py` 管流程
2. `payload_adapters.py` 管 tool-to-tool contract mapping
3. Pydantic contract 管最後 validation
4. registry metadata 協助找到對應 adapter

這樣未來新增更多 tool 時，不需要把每個 tool 的 normalization 與 validation 細節都塞進 agent graph。
