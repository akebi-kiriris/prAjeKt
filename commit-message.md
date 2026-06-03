feat: 完成 Phase 9.3~9.5 Copilot Agent 主線、雙階段確認流程與前端介面整體整理

本次提交不是單一功能，而是把前一段時間累積的 Copilot Agent 主線、
前端入口、視覺整理、測試與文件同步，一次收斂成可理解且可持續擴充的狀態。

這次的核心主題有四塊：

1. Phase 9.3：單體 Tool Registry + LangGraph Agent 最小閉環
2. Phase 9.4：`plan -> confirm -> execute` 雙階段確認執行
3. Phase 9.5：模型提案式 plan、replan 強制重新提案與二次確認
4. 前端多頁面與 timeline 子元件的版面重整、通知面板優化與測試補強

主要調整如下：

1) 後端 Copilot Agent 主線正式落地
- 新增 `backend/services/contracts/tool_inputs.py`
- 新增 `backend/services/contracts/tool_outputs.py`
- 新增 `backend/services/contracts/tool_envelopes.py`
- 新增 `backend/services/tools/registry.py`
- 新增 `backend/services/tools/handlers.py`
- 新增 `backend/services/tools/error_mapper.py`
- 新增 `backend/chains/agent_state.py`
- 新增 `backend/chains/agent_nodes.py`
- 新增 `backend/chains/agent_graph.py`
- 新增 `backend/services/agent_plan_service.py`
- 新增 `backend/services/tool_plan_service.py`
- `backend/services/copilot_service.py` 改為整合 plan / execute / reject / replan 與模型提案邏輯
- `backend/blueprints/copilot.py` 補齊：
  - `GET /api/copilot/agent/tools`
  - `POST /api/copilot/agent/plan`
  - `POST /api/copilot/agent/execute`
  - `POST /api/copilot/agent/reject`
  - `POST /api/copilot/agent/replan`

2) Agent 工具契約與執行邊界收斂
- 建立 `ToolDefinition` 與 `TOOL_REGISTRY` 白名單機制，讓 agent 只能觸達明確註冊的工具入口
- 用 `input_model` 對每個工具輸入做 schema 契約化，並提供 `input_schema` 給 plan 階段與前端使用
- 補上統一 success / failure envelope，讓工具執行結果固定回傳 `ok/data/error`
- 以 `error_mapper.py` 將例外收斂為 `error_code / retryable / hint`，供 agent 決定 retry / ask_user / stop
- 將 payload 驗證統一收斂到 registry 執行入口，不再在 handler 重複 `model_validate(...)`
- handler 改為只接收已驗證的 input model，專心處理 service 轉接與結果包裝

3) LangGraph 執行模型改為固定 graph + 動態工具序列
- 以 `agent_graph.py` 建立固定流程：
  - `intent_parse -> select -> execute -> route_error -> finalize`
- 以 `agent_nodes.py` 的 `tool_execute_node()` 統一執行每一步工具
- 多步工具流程不再靠多張業務 edge 圖硬編排，而是：
  - plan 階段先產生 `pending_tools`
  - execute 階段在同一個 execute node 內反覆取出並執行下一個工具
- `AgentState` 補齊：
  - `pending_tools`
  - `executed_tools`
  - `steps`
  - `last_result`
  - `last_error`
  - `route`
  - `created_timeline_id`
  等跨步驟共享欄位，支援工具結果透過 state 串接後續 payload

4) Phase 9.4：雙階段確認流程落地
- `execute` 階段改為只能執行既有 `plan_id`
- 在 plan store 中保存：
  - `goal`
  - `context`
  - `approved_tool_payloads`
  - `pending_tools`
  - `summary`
  - `steps_preview`
  - `risk_notes`
  - `proposal_source`
  - `proposal_reason`
- 補上 `planned / executing / succeeded / failed / rejected / expired` 狀態流轉
- execute 階段禁止覆寫已核准 `tool_payloads`，避免 preview 與實際寫入分叉

5) Phase 9.5：模型提案式 plan 與 replan 收斂
- 新增 `tool_plan_service.py`，由模型根據：
  - 工具名稱
  - 工具描述
  - side effect
  - permission note
  - input schema
  - context
  提出 `steps + payload_draft + reason`
- `create_copilot_agent_plan()` 改為：
  - 優先使用 LLM proposal
  - 失敗才 fallback `build_pending_tools`
- `replan` 改為強制模型重新提案，不再默默沿用規則 fallback
- plan API / 前端顯示新增：
  - `proposal_source`
  - `proposal_reason`
- 延遲匯入與測試啟動整理，降低 `langgraph` 對測試收集期的硬耦合

6) 前端 Copilot Agent 入口與型別同步
- 新增 `frontend/src/components/CopilotDock.vue`
- `frontend/src/services/copilotService.ts` 補齊 agent plan / execute / reject / replan / tools API
- `frontend/src/types/copilot.ts` 新增 plan/execute/replan 相關型別與步驟結果契約
- `frontend/src/App.vue` 接上全域 Copilot Agent 入口
- 前端流程改為：
  - 先輸入自然語言目標
  - 顯示計畫摘要、步驟預覽、風險提示
  - 顯示提案來源與提案理由
  - 使用者確認後才送 execute
- 隱藏不必要的內部 ID 顯示，改成使用者可理解的摘要資訊

7) 前端頁面與元件視覺整理
- 整體將多個頁面整理到較一致的視覺語言：
  - hero/header 區塊
  - 柔和背景層次
  - 更一致的卡片、表單、篩選與操作按鈕狀態
- 更新頁面包含：
  - `frontend/src/views/TasksView.vue`
  - `frontend/src/views/TimelinesView.vue`
  - `frontend/src/views/GroupsView.vue`
  - `frontend/src/views/ProfileView.vue`
  - `frontend/src/views/KnowledgeBaseView.vue`
  - `frontend/src/views/TrashView.vue`
  - `frontend/src/views/TodosView.vue`
  - `frontend/src/views/HomeView.vue`
  - `frontend/src/views/LoginView.vue`
  - `frontend/src/views/RegisterView.vue`
- timeline 相關子元件也同步整理：
  - `TimelineViewModes.vue`
  - `TimelineHeader.vue`
  - `TimelineDetailDialog.vue`
  - `TimelineKanbanBoard.vue`
  - `TimelineKanbanTaskModal.vue`
  - `TimelineCardView.vue`
  - `TimelineListView.vue`
  - `TimelineCalendarView.vue`
  - `TimelineGanttView.vue`
  - `TaskDetailPanel.vue`
  - `AiTaskGeneratePanel.vue`

8) Header / Sidebar / 通知面板體驗改善
- `frontend/src/components/Header.vue`
  - 通知面板改為較完整的通知中心樣式
  - 補上全部/未讀篩選
  - 補上刷新、全部已讀、清除已讀操作
  - 優化面板資訊密度與 hover 狀態
- `frontend/src/components/Sidebar.vue`
  - 更新桌面與手機版導覽視覺，收斂 active / hover 樣式
- `frontend/src/components/ConfirmDialog.vue`
  - 配合新 UI 風格做細節整理

9) 測試與測試設定補強
- 新增 `backend/tests/chains/test_agent_graph.py`
- 新增 `backend/tests/services/test_tool_registry.py`
- 新增 `backend/tests/services/test_copilot_plan_flow.py`
- `backend/pytest.ini` 新增 `pythonpath = .`，修正測試啟動匯入基線
- 新增 / 更新前端測試：
  - `frontend/src/services/__tests__/copilotService.test.ts`
  - `frontend/src/components/timelines/__tests__/TimelineSubcomponents.test.ts`
  - `frontend/src/components/timelines/__tests__/TimelineViewModes.test.ts`
  - `frontend/src/views/__tests__/TasksView.phase7.test.ts`
  - `frontend/src/components/__tests__/...`
  - `frontend/src/utils/__tests__/ganttPopup.test.ts`
- 新增 `frontend/src/utils/ganttPopup.ts`
- `frontend/vitest.config.ts` 補齊對應測試設定

10) 文件、README、重構計畫與進度同步
- `README.md`
  - 開發狀態更新為 Phase 9.1~9.5 已完成
  - 補上 Copilot Agent 能力說明，API 端點改集中整理到 `docs/api_endpoints.md`
- `重構計畫.md`、`進度追蹤.md`
  - 根目錄版本更新為 9.3~9.5 已完成、9.6 待進行
- `docs/重構計畫.md`、`docs/進度追蹤.md`
  - 同步對齊根目錄追蹤狀態
- `docs/api_endpoints.md`
  - 補上 Copilot Agent Phase 9.5 相關 plan / execute / reject / replan / tools 端點說明
- 更新 / 新增 Phase 9 文件：
  - `docs/Phase9_3_9_5_Agent總整理_2026-06-04.md`
  - `docs/Phase9_Agent系統設計與實作全紀錄_2026-06-04.md`
- `Phase9_Agent系統設計與實作全紀錄` 已補充：
  - registry / handler / service 分層
  - input model 與 `ConfigDict(extra="forbid")`
  - fixed graph + dynamic pending tools
  - `run_react_agent()` / `create_agent_graph()` 關係
  - `AgentState` 欄位讀寫表

驗證與檢查：
- `pytest tests/services/test_tool_registry.py tests/chains/test_agent_graph.py -q`：`10 passed`
- `pytest tests/services/test_copilot_plan_flow.py -q`：`9 passed`
- `npm run build`：PASS

補充說明：
- 這次工作樹同時包含新檔與既有檔案的大量重整，提交前建議再人工檢查：
  - `backend/blueprints/copilot.py`
  - `backend/services/copilot_service.py`
  - `backend/services/tool_plan_service.py`
  - `backend/services/tools/registry.py`
  - `frontend/src/components/CopilotDock.vue`
  - `frontend/src/views/TasksView.vue`
  - `frontend/src/components/Header.vue`
  - `docs/Phase9_Agent系統設計與實作全紀錄_2026-06-04.md`
- 本次提交範圍已跨越 agent 主線與前端整理，後續若要拆 PR，建議至少區分為：
  - Agent / 後端契約
  - 前端 Copilot 入口
  - 前端視覺整理
  - 文件同步
