## Payload Decoupling Implementation Plan

### Goal
以白名單 payload 收斂前後端契約，避免 over-posting、資料污染與畫面模型耦合 API。

### Phase 1: P0 Core Hardening (In Progress)
- [x] Task update payload 改為白名單（前端 `TaskUpdatePayload`）
- [x] Todo update payload 改為白名單（前端 `UpdateTodoPayload`）
- [x] Profile update payload 改為專用型別（前端 `ProfileUpdatePayload`）
- [x] 後端 tasks create/update 加入 unknown field reject 與欄位驗證
- [x] 後端 todos create/update 加入 unknown field reject 與欄位驗證
- [x] 後端 profile update 加入 unknown field reject

### Phase 2: Contract Alignment (Completed)
- [x] 前後端 create/update 回傳結構與 service 型別一致化
- [x] 統一 todo 回傳欄位（含 `type/priority/created_at/updated_at`）所有 endpoint
- [x] timeline update payload 與 store 層 map 做條件送出（避免空字串覆寫）

### Phase 3: Mapper Layer (Completed)
- [x] 新增 `frontend/src/utils/payloadMappers.ts`
- [x] 建立 `mapToCreateTaskPayload` / `mapToUpdateTaskPayload`
- [x] 建立 `mapToCreateTodoPayload` / `mapToUpdateTodoPayload`
- [x] view/store 一律透過 mapper 送 payload（禁止直接 spread entity）

### Phase 4: Guardrails (Completed)
- [x] 建立靜態檢查規則：禁止 `Partial<Entity>` 作為 update payload
- [x] 建立靜態檢查規則：禁止 `...entity` 直接送到 service.update
- [x] 建立 endpoint payload 規範文件（allowed/forbidden fields）

### Verification Checklist
- [x] frontend `get_errors` 無錯誤
- [x] backend `get_errors` 無錯誤
- [x] grep 無 `Partial<Todo>` / `Partial<Profile>` 舊入口
- [x] payload guardrails script（`npm run guardrails:payload`）
- [ ] API 行為測試：對 update endpoint 注入 forbidden 欄位回 400
- [ ] 回歸測試：任務、待辦、個資更新流程

### Notes
- 後端策略目前採 `reject unknown fields`（HTTP 400），可提早暴露契約偏差。
- `tasks.py` 已移除 create 時直接吃 `members` 的隱式耦合；成員請走 members API。