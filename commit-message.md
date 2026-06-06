refactor: 收斂 Agent planner/execute 體驗並同步 Phase 9 文件

本次提交聚焦 Phase 9 agent 主線的第二波收斂，不是新增全新模組，而是把已經能跑的 planner -> execute 流程補到更穩、更可觀測，也讓前端真的能把執行結果展示出來。

---

一、Planner 與執行路徑收斂

後端：

- `backend/services/tool_plan_service.py`
  - 補 LLM content block 正規化，允許模型回傳 list-style content，不再因 `.strip()` 造成 500
  - planner 輸出新增 `planning_mode`
  - prompt 補強 `create_project_only / plan_tasks_only / plan_and_create_tasks`
  - prompt 改為使用 `planner_role / workflow_group / completes_after` 協助模型理解 suggestion / apply 關係

- `backend/services/tools/registry.py`
  - 補 `planner_role`
  - 補 `workflow_group`
  - 補 `completes_after`
  - 讓 planner 不只靠工具名稱判斷，而是能理解 workflow 語意

- `backend/services/copilot_service.py`
  - plan response 補 `pending_tools`
  - execute response 補 `approved_pending_tools` / `executed_tools`
  - 補 plan / execute logging，方便直接從後端 log 判斷實際批准與執行步驟

- `backend/chains/agent_nodes.py`
  - 補 partial payload merge，降低模型只回半成品 payload 時的失敗率
  - 補 project name 推導與 `created_timeline_name` 傳遞
  - `batch_create_tasks_for_timeline` 可回收前一步 AI 生成任務作為 fallback
  - `finalize_node()` 改為輸出可讀摘要，不再永遠只回固定成功句

- `backend/chains/schemas.py`
  - `Task.priority` 改為以整數為主，並相容舊字串 priority

---

二、前端結果可見性補強

- `frontend/src/components/CopilotDock.vue`
  - 執行結果區改為顯示每個工具步驟的輸出摘要
  - `generate_timeline_tasks_with_ai` 會直接列出生成任務建議
  - `batch_create_tasks_for_timeline` 會顯示實際建立數量

- `frontend/src/types/copilot.ts`
  - 對齊新的 plan / execute 回傳欄位

這次的重點是：就算 planner 選的是 suggestion 流程，前端也不能讓它看起來像「什麼都沒做」。

---

三、文件同步

- 更新 `重構計畫.md` / `docs/重構計畫.md`
  - 將 Phase 9.5+ 已完成項目勾選完成
  - 新增 2026/06/07 的「Agent 規劃與執行體驗收斂」小節

- 更新 `進度追蹤.md` / `docs/進度追蹤.md`
  - 補上 2026/06/07 里程碑
  - 更新 Phase 9 當前狀態與下階段焦點

- 新增 `docs/future/`
  - `docs/future/README.md`
  - `docs/future/Future_AgentPrompt分域與Planner收斂方向_2026-06-07.md`
  - 作為未來 backlog / prompt 改進草稿入口

---

四、測試與驗證

後端聚焦回歸：

- `pytest backend/tests/chains/test_agent_graph.py -q`
- `17 passed`

- `pytest backend/tests/services/test_copilot_plan_flow.py backend/tests/services/test_tool_plan_service.py -q`
- `16 passed`

編譯驗證：

- `py_compile backend/chains/agent_nodes.py`
- PASS

補充：

- 前端 `CopilotDock` 測試檔已同步更新
- 本輪未重新完成 `Vitest` 執行驗證，因為這台環境先前曾出現 `spawn EPERM`

---

五、這次收斂後的效果

- planner 能更清楚區分「只建專案 / 先規劃 / 直接建任務」
- execute 結果更容易觀測與除錯
- 使用者在 UI 上能直接看到 AI 生成內容與實際建立結果
- 文件入口多了 `docs/future/`，後面想到 backlog 可以直接收納，不必先塞進 phase 主線
