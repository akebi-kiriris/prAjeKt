# Future Agent Prompt 分域與 Planner 收斂方向

## 背景

目前 `tool_plan_service.py` 的 planner prompt 已經能支撐：

1. `planning_mode` 判斷
2. 工具選擇
3. workflow 順序安排
4. 部分 payload draft 草擬

這讓現在的 agent 主線已經可用，但也開始出現一個明顯訊號：

如果未來要把更多既有函式都納進同一個 agent，單一 prompt 會越來越長，並逐步變成成本、注意力與可維護性的瓶頸。

---

## 目前問題

### 1. 工具一多，prompt 會持續膨脹

現在還在可控範圍，但若未來再加入：

1. 更多 timeline/task 工具
2. knowledge 工具
3. group / comment / snapshot 工具
4. 後續其他 domain 工具

planner prompt 會逐步變成「把整個系統說明書都給模型」。

風險：

1. token 成本上升
2. latency 增加
3. prompt 維護難度提高

---

### 2. 模型注意力會被不相關工具稀釋

即使模型能力夠強，當工具數量太多時，也容易出現：

1. 選到語意接近但不該用的工具
2. workflow 停在 suggestion，不確定要不要 apply
3. payload draft 被不同 domain 的範例干擾

---

### 3. 單一 prompt 同時承擔太多責任

現在 planner prompt 同時負責：

1. 意圖理解
2. domain 判斷
3. 工具候選縮小
4. workflow 推理
5. planning mode 決策
6. payload draft 草擬

這在早期很好推進，但長期來看會越來越難調。

---

## 建議方向

### 方向一：先做輕量 routing，再做 domain planner

把規劃流程拆成兩段：

1. `intent_router`
   - 用短 prompt 判斷這次需求屬於哪個 domain

2. `domain_planner`
   - 只拿該 domain 的工具子集做規劃

例如：

1. `timeline_task`
2. `knowledge`
3. `group_snapshot`
4. `comment_summary`

好處：

1. prompt 更短
2. 候選工具更乾淨
3. 每個 domain 的規則可以獨立調整

---

### 方向二：共通 contract 留在 shared block

目前已經開始成形的共通概念：

1. `planning_mode`
2. `planner_role`
3. `workflow_group`
4. `completes_after`
5. `suggestion / apply_suggestion / direct_write / read / analysis`

這些不需要每個 domain 都重新發明，可以保留成共享 planner contract。

建議：

1. 把共通規則維持短而穩定
2. 各 domain prompt 只補 domain 特有語意與示例

---

### 方向三：候選工具不要永遠全量注入

不一定要每次把全部 registry 都丟給 planner。

可以改成：

1. 先根據 router 結果挑 domain
2. 再根據 domain 載入工具子集
3. 最後才交給 planner 決策

這仍然是 model-led，不是回到單純 keyword hardcode。

---

### 方向四：未來可考慮 page-scoped agent

如果前端未來不同頁面本來就有不同工作語境，可以考慮：

1. timeline 頁面掛 `timeline agent`
2. knowledge 頁面掛 `knowledge agent`
3. group 頁面掛 `group agent`

這樣每個 agent：

1. prompt 更短
2. context 更穩定
3. 測試邊界更清楚

---

## 可行拆分草案

### A. router 層

檔案可考慮：

1. `backend/services/tool_intent_router.py`

責任：

1. 判斷主要 domain
2. 判斷是否需要多 domain workflow
3. 回傳候選工具群組

---

### B. planner 層

現有：

1. `backend/services/tool_plan_service.py`

未來可調整為：

1. shared planner prompt builder
2. domain planner prompt builder
3. planner output validator

---

### C. registry metadata 層

現有：

1. `backend/services/tools/registry.py`

未來可再擴充：

1. `domain`
2. `page_scope`
3. `input_shape_kind`
4. `requires_existing_entity`

這些欄位可幫助 router 與 planner 更穩定縮小候選工具。

---

## 建議實作順序

### Step 1

先不動 execute graph，只補 `domain` metadata 與 planner prompt 結構整理。

目標：

1. 保持目前功能可用
2. 先讓 registry 與 prompt 更容易拆

---

### Step 2

新增 `intent_router`，但先只做單一 domain 分流，不急著處理複合 domain。

目標：

1. 先驗證 prompt 縮短的實際效果
2. 驗證 planner 成功率是否提高

---

### Step 3

依前端頁面逐步引入 page-scoped agent 或 domain-specific agent。

目標：

1. 控制 prompt 膨脹
2. 讓 agent 更像頁面內的工作助手，而不是全域萬能入口

---

## 暫時不急著做的事

1. 一開始就做複雜 multi-agent orchestration
2. 一開始就做太細的 tool embedding retrieval
3. 先把每個 domain 都拆成獨立 service

先把：

1. router
2. planner 分域
3. registry metadata

這三件事穩定，比較務實。

---

## 結論

目前單一 planner prompt 還能撐住，但它不應該無限制長大。

比較健康的方向不是一直堆 prompt，而是逐步收斂成：

1. 短 router
2. 分域 planner
3. 共通 contract
4. 縮小候選工具集合

這樣未來 agent 即使納入更多現有函式，也比較不容易在成本、注意力與維護性上一起失控。
