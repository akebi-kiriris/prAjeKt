feat: 新增 agent trace 基線並推進 Phase 10 契約收斂

這次提交把兩條原本分散的主線正式收進同一波交付：一條是 `Phase 9.6` 的 trace-only 前置項，先為 agent 的 `plan / reject / execute / replan` 補上最小可追蹤能力；另一條是 `Phase 10` 的全系統契約收斂，先完成第一輪契約地圖盤點、前後端型別 / response 對齊，以及後端契約來源收斂規劃。

---

一、Agent trace-only 前置基線

- 新增：
  - `backend/services/agent_trace_service.py`

- 調整：
  - `backend/blueprints/copilot.py`
  - `backend/services/copilot_service.py`
  - `backend/chains/agent_graph.py`
  - `backend/chains/agent_nodes.py`
  - `backend/chains/agent_state.py`
  - `backend/tests/services/test_copilot_plan_flow.py`
  - `backend/tests/chains/test_agent_graph.py`

- 本輪收斂重點：
  - 為 agent 操作補上 `request_id` / `plan_id` 串接
  - 建立 in-memory trace 結構，記錄 route、event、status、duration、error_code
  - 讓 `plan / reject / execute` 與 graph node 都能寫入一致欄位的 trace event
  - 在 service response 中回傳 `request_id` 與 `trace`，方便前端與後續 Phase 12/13 延伸

---

二、Phase 10.1 第一批前後端契約對齊

- 調整：
  - `frontend/src/services/taskService.ts`
  - `frontend/src/types/task.ts`
  - `frontend/src/components/timelines/TimelineViewModes.vue`
  - `frontend/src/components/timelines/__tests__/TimelineViewModes.test.ts`
  - `frontend/src/services/groupService.ts`
  - `frontend/src/types/group.ts`
  - `frontend/src/stores/groups.ts`
  - `frontend/src/stores/__tests__/groups.test.ts`
  - `frontend/src/views/GroupsView.vue`
  - `frontend/src/services/notificationService.ts`
  - `frontend/src/services/timelineService.ts`
  - `frontend/src/services/todoService.ts`
  - `frontend/src/services/trashService.ts`
  - `frontend/src/types/copilot.ts`
  - `frontend/src/services/__tests__/taskService.test.ts`

- 本輪對齊內容：
  - `tasks` 子任務 response envelope 改以 `message + subtask` 對齊後端
  - `task tags` 支援字串輸入並在送出前正規化為陣列或 `null`
  - `groups` create / join / leave / sendMessage response shape 改為明確契約型別
  - `notifications` / `timelines` / `todos` / `trash` 的 mutation response 改回明確 envelope
  - `copilot` 前端型別補上 `request_id` 與 `trace`
  - 移除前端高風險 cast，改用可追的正式型別

---

三、Phase 10 文件與契約來源規劃

- 新增：
  - `docs/phases/Phase10_契約收斂與前後端對齊規劃_2026-06-12.md`
  - `docs/phases/Phase10_1_全系統契約盤點基線規劃_2026-06-12.md`
  - `docs/phases/Phase10_2_後端契約來源收斂規劃_2026-06-12.md`
  - `docs/reference/backend_契約來源索引.md`

- 更新：
  - `docs/phases/Phase9_6_Agent可觀測性與評測基線規劃_2026-06-02.md`
  - `docs/重構計畫.md`
  - `docs/進度追蹤.md`

- 文件收斂重點：
  - 將 9.6 明確改為 trace-only 前置項，evaluation 與 observability 延後到 Phase 12/13
  - 將 Phase 10 重新定位為全系統前後端契約維護 phase，而非只偏 agent
  - 為 Phase 10 補上 10.1、10.2、10.6、10.7 的收斂順序、完成定義與執行護欄

---

四、README 與 docs 目錄規範整理

- 更新：
  - `backend/README.md`
  - `backend/blueprints/README.md`
  - `backend/chains/README.md`
  - `backend/migrations/README.md`
  - `backend/models/README.md`
  - `backend/prompts/README.md`
  - `backend/realtime/README.md`
  - `backend/repositories/README.md`
  - `backend/scripts/README.md`
  - `backend/scripts/backfill/README.md`
  - `backend/scripts/db/README.md`
  - `backend/scripts/diagnostics/README.md`
  - `backend/services/README.md`
  - `backend/services/contracts/README.md`
  - `backend/services/tools/README.md`
  - `backend/tests/README.md`
  - `frontend/src/README.md`
  - `frontend/src/components/README.md`
  - `frontend/src/components/__tests__/README.md`
  - `frontend/src/components/timelines/README.md`
  - `frontend/src/composables/README.md`
  - `frontend/src/router/README.md`
  - `frontend/src/services/README.md`
  - `frontend/src/stores/README.md`
  - `frontend/src/styles/README.md`
  - `frontend/src/types/README.md`
  - `frontend/src/utils/README.md`
  - `frontend/src/views/README.md`
  - `docs/README.md`
  - `docs/future/README.md`
  - `docs/workflows/README.md`

- 刪除：
  - `docs/Phase9_2_Docstring規範化規劃_2026-05-30.md`
  - `docs/phase9_2_error_semantics_matrix.md`
  - `docs/phase9_2_tool_entrypoints.md`
  - `docs/phase9_2_tool_schema_contracts.md`

- 本輪整理方向：
  - 統一 backend / frontend / docs 目錄說明語氣與責任邊界
  - 讓 README 更像持續維護的入口文件，而不是只保留一次性整理筆記
  - 清掉已不適合留在 `docs/` 根層的舊 phase9.2 文件

---

五、驗證

- `python -m pytest backend/tests/services/test_copilot_plan_flow.py backend/tests/chains/test_agent_graph.py -q`
  - PASS（37 passed）
- `npm run build`
  - PASS
- `npm run test -- taskService.test.ts groups.test.ts TimelineViewModes.test.ts`
  - PASS（18 passed）

---

六、補充

- 這次提交同時包含行為收斂與文件收斂，但主題一致，都是為了讓 agent trace 與 Phase 10 契約治理有穩定地基
- `agent_trace_service` 目前採用 lightweight in-memory 方式，先滿足 trace-only 前置需求；更完整的持久化與指標化收斂留待後續 phase
