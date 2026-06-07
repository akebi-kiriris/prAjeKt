refactor: 收斂 backend 結構並補強前後端契約驗證

這次提交主要做兩件事：一是把 `backend/` 根層的維護型腳本與目錄說明收斂到較清楚的結構；二是補強 task / timeline 相關 API 的前後端契約，讓 request / response shape 與測試覆蓋更一致。

---

一、backend 結構整理

- 新增 backend 目錄層 README
  - `backend/README.md`
  - `backend/models/README.md`
  - `backend/prompts/README.md`
  - `backend/realtime/README.md`
  - `backend/migrations/README.md`
  - `backend/tests/README.md`
  - `backend/scripts/README.md`
  - `backend/scripts/backfill/README.md`
  - `backend/scripts/db/README.md`
  - `backend/scripts/diagnostics/README.md`

- 將維護型 / 一次性腳本移出 `backend/` 根層
  - `backfill_task_users.py` → `backend/scripts/backfill/`
  - `backfill_timeline_users.py` → `backend/scripts/backfill/`
  - `check_tables.py` → `backend/scripts/diagnostics/`
  - `create_missing_tables.py` → `backend/scripts/db/`
  - `init_db.py` → `backend/scripts/db/`

- 同步更新相關 runbook 路徑
  - `docs/runbooks/Phase5_1_PostgreSQL遷移流程.md`
  - `docs/runbooks/Phase5_2_Railway後端部署.md`
  - `docs/runbooks/Phase6_0_開發資料庫遷移流程.md`

---

二、task / timeline API 契約補強

- 修正 `POST /timelines/{id}/conflict-check` payload 契約
  - `TimelineConflictPayload` 補上 `task_id`
  - 對齊前端既有的 `ConflictCheckPayload`
  - 讓「編輯 / 指派既有任務時排除自己衝突」可正確運作

- 調整新增成員 API 的成功回傳內容
  - `POST /tasks/{id}/members`
  - `POST /timelines/{id}/members`
  - 原本只回 `{ message }`
  - 現在改為真的回傳新增後的成員資料，與前端 `TaskMember` 型別對齊

---

三、前端 payload type 收斂

- `frontend/src/types/task.ts`
  - 新增 `TaskPriority = 1 | 2 | 3`
  - `CreateTaskPayload.end_date` 改為必填
  - `priority` 改為 `TaskPriority`

- `frontend/src/types/timeline.ts`
  - `ConflictCheckPayload.start_date` / `end_date` 改為必填
  - `priority` 改為 `TaskPriority`

- `frontend/src/utils/payloadMappers.ts`
  - `mapToCreateTaskPayload()` 現在缺少 `end_date` 會直接中止
  - `priority` 只接受 `1 | 2 | 3`
  - update payload 的 priority 也同步收斂

- `frontend/src/components/timelines/TimelineDetailDialog.vue`
  - conflict-check payload 若未填 `start_date`，會以 `end_date` 回填
  - AI 批次建立任務前，會先將 `priority` 正規化為 `1 | 2 | 3`

---

四、契約測試補齊

- 新增 / 強化以下高風險 endpoint 的 blueprint 契約測試：
  - `POST /tasks`
  - `POST /tasks/{id}/members`
  - `POST /timelines/{id}/members`
  - `POST /timelines/{id}/conflict-check`
  - `POST /timelines/{id}/batch-create-tasks`

- 每條至少補到：
  - 缺欄位
  - 錯型別
  - 成功 body 結構

---

五、驗證

- `pytest backend/tests/blueprints/test_tasks.py backend/tests/blueprints/test_timelines.py -q`
  - `38 passed`

- `python -m py_compile backend/blueprints/tasks.py backend/blueprints/timelines.py backend/services/task_service.py backend/services/timeline_service.py`
  - PASS

- `npm run build`
  - PASS

- `npm run test -- payloadMappers.test.ts taskService.test.ts timelineService.test.ts`
  - 本機環境仍受 `spawn EPERM` 影響，未能完成 Vitest 啟動

---

六、補充

- 本次重點是「契約對齊 + 結構整理」，不是新增產品功能
