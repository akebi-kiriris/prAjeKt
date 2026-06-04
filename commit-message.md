refactor: 收斂 Agent 契約邊界並整理 docs 結構

本次提交整合兩條主線：

1. Phase 9.5 後續補強
2. docs 目錄結構整理與主文件同步

目標不是新增一個全新功能，而是把已經落地的 Agent 主線補到更一致、更安全、更容易維護，同時把文件入口整理成之後能持續使用的樣子。

---

一、Agent 契約一致性與安全邊界補強

後端：

- `backend/blueprints/copilot.py`
  - `/agent/replan` 正式接收並傳遞 `tool_payloads`
- `backend/services/copilot_service.py`
  - `tool_payloads` 合併改為深層合併，避免模型 draft 蓋掉前端已提供內容
  - `create_copilot_agent_plan()` 補上 plan steps 上限守門
- `backend/services/tool_plan_service.py`
  - planner prompt 明示 protected keys（`user_id`、`timeline_id`、`task_id`、`group_id` 等）不可由模型填入
  - plan steps 增加長度上限，超過直接拒絕
- `backend/services/tools/registry.py`
  - registry 補上 handler exception boundary
  - 即使 handler 漏包例外，仍會統一映射為標準 failure envelope
- `backend/chains/agent_nodes.py`
  - 改為防禦式讀取 `steps` / `output`
  - 降低 malformed state 造成 `KeyError` / 500 的風險
- `backend/services/contracts/tool_envelopes.py`
  - `ToolSuccess.ok` / `ToolFailure.ok` 收斂為 `Literal[True/False]`
- `backend/services/contracts/task_contracts.py`
  - `TaskCreateInput` 的 mutable default list 改為 `Field(default_factory=list)`
- `backend/services/contracts/tool_inputs.py`
  - `UpdateTaskToolInput` 補入 `actor_user_id`
- `backend/services/task_service.py`
  - `create_notification()` 由靜默吞錯改為 warning log
  - `update_task_for_member()` 改為接受 `operator_user_id`，並在 service 內驗證權限
- `backend/services/timeline_service.py`
  - `update_timeline_for_member()` 改為接受 `operator_user_id`，並在 service 內驗證權限
- `backend/services/tools/handlers.py`
  - update task handler 改由 context actor 注入 service
- `backend/blueprints/tasks.py`
  - task update route 改為傳入 JWT user_id
- `backend/blueprints/timelines.py`
  - timeline update route 改為傳入 JWT user_id

前端：

- `frontend/src/types/copilot.ts`
  - `CopilotAgentPlanPayload` / `CopilotAgentReplanPayload` 補上 `tool_payloads`
  - `CopilotAgentExecuteByPlanPayload` 移除 `tool_payloads`
- `frontend/src/components/CopilotDock.vue`
  - `plan` / `replan` 路徑統一帶入 `tool_payloads`

測試：

- `backend/tests/services/test_copilot_plan_flow.py`
  - 補 plan payload deep merge 測試
  - 補 steps 上限拒絕測試
- `backend/tests/services/test_tool_registry.py`
  - 補 handler exception 由 registry 映射為 failure envelope 的測試
- `backend/tests/services/test_task_service.py`
  - 補 task update 未授權 operator 測試
- `backend/tests/services/test_timeline_service_access.py`
  - 補 timeline update 未授權 operator 測試
- `backend/tests/chains/test_agent_graph.py`
  - 補 malformed step 不應造成 finalize crash 的測試
- `frontend/src/components/__tests__/CopilotDock.test.ts`
  - 對齊 `plan` / `replan` payload shape
- `frontend/src/services/__tests__/copilotService.test.ts`
  - 對齊 `plan` / `replan` service payload shape

---

二、docs 結構整理與文件同步

- 調整 `docs/` 結構，將 phase / reference / guides / runbooks / architecture 等內容移到對應資料夾
- 清掉舊路徑殘留的 Phase 9.2 與 reference 類文件位置
- 更新 `README.md`
  - 開發狀態改為反映「9.5 主線 + 9.5 後續補強已完成」
  - `Copilot Agent` 說明補上契約與安全邊界補強
  - `核心工程文件` 段落改成新 docs 路徑
- 更新 `重構計畫.md` / `docs/重構計畫.md`
  - 將 2026/06/05 的 9.5 後續補強從「規劃」改為「完成」
  - 補上實際完成項目與驗證結果
- 更新 `進度追蹤.md` / `docs/進度追蹤.md`
  - 補上 2026/06/05 里程碑
  - 將當前焦點更新為「9.5 後續補強完成，下一步 9.6」

---

三、驗證結果

後端聚焦回歸：

- `pytest tests/services/test_copilot_plan_flow.py tests/services/test_tool_registry.py tests/services/test_task_service.py tests/services/test_timeline_service_access.py tests/chains/test_agent_graph.py -q`
- `46 passed`

前端聚焦回歸：

- `npm run test -- copilotService.test.ts CopilotDock.test.ts`
- `11 passed`

Build：

- `npm run build`
- PASS

---

四、備註

- 本次提交不改 Agent 主線 UX（仍維持 `plan -> confirm -> execute`）
- 本次重點在於：
  - 契約對齊
  - 防禦性補強
  - service 權限邊界補洞
  - 文件入口整理
- Phase 9 下一步銜接 9.6：trace、benchmark、評測報表與工具覆蓋擴充
