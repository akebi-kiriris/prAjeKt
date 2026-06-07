# Phase 9.2：Docstring 規範化規劃

> 日期：2026-05-30  
> 階段定位：Phase 9 第二階段（可讀性與契約描述補齊）  
> 前置條件：Phase 9.1 Type Hints 基線已完成

---

## 目標

1. 統一後端 docstring 風格（Google style）。
2. 補齊 service 對外函式的契約描述（用途、輸入、回傳、錯誤）。
3. 明確標註 tool-facing public API 邊界（可調用/不可調用）。
4. 讓 agent/tool 串接時可直接依函式註解理解行為邊界與副作用。
5. 為 9.3 單體後端 tool registry 提供穩定契約基線。

---

## 非目標（9.2 不做）

1. 不改 business logic 與 API 契約。
2. 不做新功能開發或流程重構。
3. 不追求每個私有 helper 都寫長註解（僅必要者）。

---

## Docstring 規範（Google Style）

每個目標函式至少包含：

1. 一句話摘要（做什麼）。
2. `Args:` 參數與重要限制。
3. `Returns:` 回傳型別與語義。
4. `Raises:` 可預期錯誤與觸發情境。

撰寫原則：

1. 描述「行為契約 + 邊界」而非逐行解釋。
2. 避免重複 type hints 已明示內容。
3. 錯誤情境用 domain 語言（例：`TaskOperationError`）。
4. 補充副作用說明（是否寫 DB / 發通知 / 呼叫 AI / 檔案 IO）。

---

## Agent 契約導向補充（9.2 新增）

### A. 可調用邊界（tool-facing）

1. 每個 service 的對外函式標示可否作為 agent 調用入口。
2. `_` 開頭 helper 一律視為 internal，不進入 tool registry。
3. 對外函式需補前置條件（權限、必要參數、上下文）。

### B. 輸入/輸出穩定性

1. 對外函式輸入優先使用既有 Pydantic contract（可逐步補齊）。
2. 回傳結構避免同函式多型（例如時而回 `int`、時而回 `dict`）。
3. 對回傳欄位補語義描述（不是只寫型別）。

### C. 錯誤碼與可重試語意

1. 例外描述需能對應 `error_code`（逐步收斂，不要求一次到位）。
2. 標示是否可重試（retryable）與建議下一步（hint）。
3. 讓 LangGraph 可依錯誤語意做分支（重試/追問/終止）。

---

## 9.2 產出物（做完即可銜接 9.3）

### 產出物 A：Tool Entrypoint 清單

1. 檔案位置：`docs/phases/phase9_2_tool_entrypoints.md`。
2. 每個 service 至少列出：
   - `function_name`
   - `exposed_to_agent`（`yes/no`）
   - `preconditions`（權限/必要上下文）
   - `side_effects`（DB 寫入/通知/AI/檔案 IO）
3. 規則：`_` 開頭函式預設 `exposed_to_agent=no`，除非特例註記。

### 產出物 B：Schema 契約對照表

1. 檔案位置：`docs/phases/phase9_2_tool_schema_contracts.md`。
2. 每個 entrypoint 至少列出：
   - `InputSchema`（Pydantic 類別或待補）
   - `OutputSchema`（固定成功結構）
   - `ErrorSchema`（`error_code/message/retryable/hint`）
3. 規則：避免同函式多型回傳（例如同時回 `int` 與 `dict`）。

### 產出物 C：錯誤語意矩陣

1. 檔案位置：`docs/phases/phase9_2_error_semantics_matrix.md`。
2. 至少覆蓋：
   - `VALIDATION_ERROR`
   - `PERMISSION_DENIED`
   - `NOT_FOUND`
   - `CONFLICT`
   - `UPSTREAM_TIMEOUT`
   - `UPSTREAM_UNAVAILABLE`
3. 每個錯誤碼需定義：
   - `retryable`（`true/false`）
   - `langgraph_route`（`retry` / `ask_user` / `stop`）
   - `agent_hint`（建議下一步）

---

## 實作範圍

### 第一波（優先）

1. `backend/services/task_service.py`
2. `backend/services/timeline_service.py`
3. `backend/services/group_service.py`
4. `backend/services/message_service.py`
5. `backend/services/knowledge_service.py`

目標：先覆蓋對外公開函式（非 `_` 開頭）。

### 第二波（補齊）

1. `backend/services/auth_service.py`
2. `backend/services/profile_service.py`
3. `backend/services/todo_service.py`
4. `backend/services/notification_service.py`
5. `backend/services/rag_planning_service.py`
6. `backend/services/mcp_bridge_service.py`
7. `backend/services/trash_service.py`
8. `backend/services/critical_path_service.py`

---

## 工作拆解

### Step 1：建立統一模板

1. 定義本專案 Google style 最小模板。
2. 選 2~3 支 service 做樣板函式。
3. 鎖定中英混用規則（建議：註解中文、關鍵術語英文）。
4. 決定 docstring 第一段固定格式：
   - `用途`
   - `前置條件`
   - `副作用`

### Step 2：第一波核心 service 補齊

1. 以公開函式為單位補 docstring。
2. 每支檔案完成後跑對應測試，確認無行為變更。
3. 特別補齊 `Raises`，避免 agent 端誤判錯誤路徑。
4. 同步標記 entrypoint（`exposed_to_agent=yes/no`）。

### Step 3：第二波 service 補齊

1. 延續同模板完成剩餘 service。
2. 對回傳 payload 較複雜函式補「欄位語義」說明。
3. 收斂回傳形狀差異（先記錄差異，9.3 實作統一 envelope）。

### Step 4：一致性檢查與收尾

1. 抽查每檔是否存在風格不一致。
2. 移除無資訊量註解（流水帳）。
3. 同步 `重構計畫.md`、`進度追蹤.md`。
4. 輸出 tool-facing 函式清單（供 9.3 registry 直接引用）。
5. 產出 schema 契約對照表與錯誤語意矩陣。

---

## 9.2 執行清單（可勾選）

- [x] 完成 `tool entrypoints` 清單（含前置條件與副作用）
- [x] 完成 `Input/Output/Error schema` 對照表
- [x] 完成 `error_code -> retryable -> route` 矩陣
- [ ] 核心 service docstring 補齊並對齊模板
- [ ] 次核心 service docstring 補齊並對齊模板
- [ ] 測試通過且無行為變更

---

## 驗收標準（9.2 完成定義）

1. `backend/services/*` 對外函式 docstring 覆蓋率達成（公開函式全覆蓋）。
2. 每個目標函式皆有 `Args/Returns/Raises`（必要時可簡化）。
3. 測試綠燈且無功能行為變更。
4. 文件狀態同步更新。
5. 可產出「service 對外函式 -> 契約摘要」清單，供 LangGraph 節點映射。
6. 完成三份前置文件：
   - `docs/phases/phase9_2_tool_entrypoints.md`
   - `docs/phases/phase9_2_tool_schema_contracts.md`
   - `docs/phases/phase9_2_error_semantics_matrix.md`

---

## 風險與對策

1. 風險：註解過長造成維護成本上升。  
   對策：每個區塊維持最小必要資訊，避免敘事化。

2. 風險：註解與程式行為漂移。  
   對策：只描述穩定契約，避免寫實作細節。

3. 風險：一次修改檔案過多導致 review 困難。  
   對策：分波提交（核心 service 一波、其餘一波）。

---

## 建議提交策略

1. Commit A：模板 + 第一波核心 service docstring。
2. Commit B：第二波 service docstring + 一致性清理。
3. Commit C：tool-facing 清單與契約摘要（9.3 前置）。
4. Commit D：文件同步（`重構計畫.md` / `進度追蹤.md`）。
