# Future：magic numbers 與設定常數盤點

> 日期：2026-06-29  
> 狀態：future backlog  
> 來源：Agent / AI 任務生成除錯後，發現部分數字容易被記成業務規則，但實際可能只是範例、測試值或流程限制

---

## 1. 背景

目前專案內已有不少數字散落在 service、chain、prompt、frontend component、test 與文件中。

其中有些是合理常數，例如：

1. Agent planner 最大步數
2. Agent execute 最大 loop 次數
3. RAG retrieval top-k
4. 上傳檔案大小上限
5. 快取 TTL
6. UI 顯示前幾筆資料

但也有些數字只是：

1. 文件範例
2. 測試資料
3. UI 文案範例
4. prompt 內的建議範圍
5. 早期設計留下來但已不代表現行規則的描述

如果沒有分類，很容易把「範例數字」誤認成「系統規則」，或把真正需要命名的 hard-coded value 留在程式裡。

---

## 2. 觸發案例：AI 生成任務是否固定 6 個

曾經有印象是 AI 生成任務數量可能固定為 6 個。

目前只讀檢查後的初步結論：

1. `generate_timeline_tasks_with_ai` 目前沒有固定生成 6 個任務
2. prompt 目前只寫「生成數個完整的任務」，沒有明確要求 6 個
3. service 以 `len(generated_tasks)` 回傳實際 `generatedCount`
4. 文件中有舊範例寫「AI 生成 6 個新任務」或「已建立 1 個專案、6 個任務」
5. 程式中的 `6` 更明確出現在 Agent 流程限制，例如 `MAX_PLAN_STEPS = 6`、`max_loops = 6`

所以「AI 任務生成固定 6 個」目前比較像舊文件 / 範例造成的印象，而不是現行程式規則。

這類情況很適合納入 magic number / hard-coded value 盤點：不是看到數字就改，而是先確認它到底屬於哪一類。

---

## 3. 名詞分類

### 3.1 magic number

沒有名稱、沒有脈絡、直接出現在邏輯中的數字。

例如：

```python
if retry_count >= 2:
    ...
```

如果 `2` 是 retry limit，就應該考慮命名。

---

### 3.2 hard-coded value

硬寫在程式內的值。

它不一定錯，但需要判斷：

1. 是否會改
2. 是否跨檔重複
3. 是否代表業務規則
4. 是否應由環境變數或設定檔控制

---

### 3.3 business rule constant

真正代表業務或流程規則的常數。

例如：

1. `MAX_PLAN_STEPS`
2. `max_loops`
3. upload size limit
4. retrieval top-k
5. cache TTL

這類值應該有清楚命名、集中來源與測試覆蓋。

---

### 3.4 example number

文件、prompt example 或 response 範例裡的數字。

例如：

1. 「AI 生成 6 個新任務」
2. 「現有 2 個任務」
3. 「已建立 1 個專案」

這類數字不一定要抽常數，但需要避免文字讓人誤會成現行規格。

---

### 3.5 test fixture number

測試資料使用的數字。

例如：

1. `timeline_id = 39`
2. `task_id = 1001`
3. `max_loops=3`

這類數字通常不用抽成 production constant，但如果測試在驗證某個規則上限，應該引用正式常數，避免測試與實作漂移。

---

## 4. 建議盤點分類

### 4.1 Agent limits

候選項目：

1. `MAX_PLAN_STEPS`
2. `max_loops`
3. retry limit
4. plan TTL
5. trace metadata 中的 limit

檢查重點：

1. 是否有單一來源
2. 前端與後端是否重複硬寫
3. OpenAPI 是否有描述上限
4. 測試是否引用正式常數或至少覆蓋邊界

---

### 4.2 AI / RAG limits

候選項目：

1. `RAG_RETRIEVAL_TOP_K`
2. `max_sources`
3. LLM timeout
4. LLM max tokens
5. prompt 內的建議數量或建議天數

檢查重點：

1. 哪些應由 env 控制
2. 哪些應寫成 module constant
3. 哪些只是 prompt guidance
4. fallback 與正常路徑是否使用同一組限制

---

### 4.3 Timeline / task workflow limits

候選項目：

1. AI 生成任務建議數量
2. batch create 任務數量上限
3. dependency chain 長度
4. conflict check sample tasks
5. weekly report 顯示前幾項 pending / risk tasks

檢查重點：

1. 是否已有明確上限
2. 若沒有，是否需要補
3. 若只在 UI slice，是否需要命名
4. 是否會影響使用者可見行為

---

### 4.4 UI display limits

候選項目：

1. list preview 顯示前幾筆
2. toast / panel 顯示前幾個 item
3. chart / dashboard 顯示前幾名
4. mobile / desktop layout threshold

檢查重點：

1. 是否只是呈現策略
2. 是否跨元件重複
3. 是否應搬到 UI constants
4. 是否需要和 backend response limit 分開

---

### 4.5 Infra / safety limits

候選項目：

1. upload max MB
2. cache TTL
3. job TTL
4. background executor max workers
5. notification polling interval

檢查重點：

1. 是否應由 env 設定
2. 是否有最小 / 最大 clamp
3. 是否有文件說明預設值
4. 是否有測試覆蓋非法設定

---

## 5. 不建議的盤點方式

### 5.1 不建議直接搜所有數字後全部抽常數

單純搜尋數字會抓到大量不該改的內容：

1. 日期
2. ID fixture
3. HTTP status code
4. 測試資料
5. 文件章節編號
6. UI class / CSS spacing
7. migration revision

這會製造大量雜訊。

---

### 5.2 不建議把所有數字都搬到同一個 constants.py

全域 constants 會很快變成雜物間。

比較好的方式是依 domain 放置：

1. Agent 常數靠近 agent / planner
2. RAG 常數靠近 rag planning
3. Knowledge upload 常數靠近 knowledge service
4. UI display 常數靠近 frontend utils / component domain

---

### 5.3 不建議把 prompt example 數字當成正式規格

Prompt 或文件中的範例數字應標明是 example。

若數字真的是規格，應該回到程式常數與測試，而不是只存在 prompt 文字中。

---

## 6. 建議實作順序

### Step 1：先盤點高風險主線

優先看：

1. Agent limits
2. AI / RAG limits
3. Timeline / task workflow limits

原因是這些數字會直接影響 AI 行為、tool chaining、使用者看到的結果與除錯判斷。

---

### Step 2：建立分類表

每個項目至少記錄：

1. 數值
2. 位置
3. 類型：business rule / config / UI display / example / test fixture
4. 是否跨檔重複
5. 是否需要抽常數
6. 是否需要文件化
7. 是否需要測試

---

### Step 3：只處理真正需要收斂的值

優先處理：

1. 跨前後端重複的數字
2. 影響契約或 user-visible 行為的數字
3. 已經造成誤解的範例數字
4. 和安全 / 成本 / timeout 有關的數字

---

### Step 4：再決定是否進入正式 phase

如果盤點後只是少量 cleanup，可以直接放到後續維護。

如果發現大量限制值會影響 Agent / AI 行為，應考慮納入正式 Phase，並配合測試與文件更新。

---

## 7. 候選檢查指令

這些指令只適合輔助，不代表完整結論：

```powershell
rg -n "MAX_|max_|limit|top_k|ttl|timeout|retry|slice\\(|\\[:\\d+\\]" backend frontend/src docs
```

```powershell
rg -n "6 個|6個|六個|最多.*6|任務.*6|AI 生成.*任務" backend frontend/src docs
```

```powershell
rg -n "os\\.getenv|import\\.meta\\.env|VITE_|TTL|TIMEOUT|MAX" backend frontend/src
```

檢查時要人工分流，不應直接照搜尋結果批量修改。

---

## 8. 初步候選清單

目前已知可先回頭看的項目：

1. `backend/services/tool_plan_service.py`
   - `MAX_PLAN_STEPS = 6`
   - 目前已是命名常數，但要確認前端 execute `max_loops` 是否同源或刻意分開

2. `backend/chains/agent_graph.py`
   - `max_loops: int = 6`
   - 需要判斷是否應與 `MAX_PLAN_STEPS` 共享或各自命名

3. `backend/blueprints/copilot.py`
   - `max_loops = data.get('max_loops', 6)`
   - 若維持預設值，最好引用同一來源

4. `frontend/src/components/CopilotDock.vue`
   - `max_loops: 6`
   - 前端是否應由後端預設處理，或明確使用 shared client constant

5. `backend/services/rag_planning_service.py`
   - `max_sources` 預設與 clamp
   - `RAG_RETRIEVAL_TOP_K`
   - history / knowledge split limit

6. `backend/services/knowledge_service.py`
   - `KNOWLEDGE_UPLOAD_MAX_MB`
   - list limit 預設

7. `backend/services/group_service.py`
   - snapshot job TTL
   - max records
   - summary item truncation

8. docs examples
   - 「AI 生成 6 個新任務」
   - 「已建立 1 個專案、6 個任務」
   - 需要標成範例，或避免像正式規格

---

## 9. 結論

後續確實應該盤點 magic numbers / hard-coded limits，但重點不是把所有數字抽出來。

比較健康的目標是：

1. 找出真正代表規則的數字
2. 給它們清楚名稱與單一來源
3. 區分程式規則、prompt guidance、UI display、test fixture、文件範例
4. 避免舊文件範例讓人誤會現行系統行為

這件事適合先放在 future backlog，等 Agent / AI 主線再新增工具或做 Phase 級整理時一起處理。
