fix: 修正 Copilot Agent 前端執行契約與看板篩選狀態不一致

本次提交針對 code review 指出的兩個前端問題做最小修補，
不調整整體 Phase 9 agent 流程，只收斂明確不一致的 API 契約與 UI 計數邏輯。

主要調整：

1) 移除前端錯誤的 `executeAgent()` 直接執行入口
- `frontend/src/services/copilotService.ts`
  - 移除 `executeAgent(payload)` 方法
- `frontend/src/types/copilot.ts`
  - 移除已不符合後端 `/api/copilot/agent/execute` 實際契約的 `CopilotAgentExecutePayload`
- `frontend/src/services/__tests__/copilotService.test.ts`
  - 移除對 `executeAgent()` 的錯誤映射測試

原因：
- 後端 `POST /api/copilot/agent/execute` 目前已強制要求 `plan_id + confirm`
- 前端保留 `message/context -> execute` 的舊方法，會造成誤用時必然得到 400
- 畫面主流程已經改為：
  - `createAgentPlan()`
  - `executeAgentPlan()`
  - `rejectAgentPlan()`
  - `replanAgent()`
  因此移除錯誤入口比繼續保留更安全

2) 修正 Timeline 看板篩選狀態計數邏輯
- `frontend/src/components/timelines/TimelineViewModes.vue`
  - 將 `activeFilterCount` 改為與 `hasActiveFilters` 使用相同條件：
    - `filterPriority.value !== null`
    - `filterTag.value.trim().length > 0`

修正結果：
- 當 tag 只輸入空白時，不再出現：
  - `hasActiveFilters = false`
  - 但 `activeFilterCount = 1`
  的顯示不一致問題

驗證：
- `npm run build`：PASS
