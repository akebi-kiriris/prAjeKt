refactor: 完成 Phase 10.6 已知鬆動點實作清理

這次提交完成 Phase 10.6，主軸是接續 10.4 契約狀態矩陣與 10.5 模組別主線導覽，把已知會造成閱讀成本、型別漂移或契約鬆動的區塊逐批收斂。這輪沒有展開新產品功能，而是聚焦 frontend service 邊界、group snapshot schema、tool output 契約、測試 fixture 型別與文件狀態同步。

---

一、Phase 10.6 規劃與 docs 目錄規範

- 新增：
  - `docs/phases/Phase10_6_已知鬆動點實作清理規劃_2026-06-18.md`
  - `docs/phases/README.md`
  - `docs/reference/README.md`
  - `docs/guides/README.md`
  - `docs/runbooks/README.md`
  - `docs/architecture/README.md`
  - `docs/learning/README.md`
  - `docs/changelog/README.md`

- 本輪整理重點：
  - 將 10.6 定位為「已知鬆動點實作清理」，不重新盤點整個 Phase 10
  - 將 10.6 拆成五批：
    - frontend service 邊界
    - timeline AI / RAG schema 判定
    - groups / messages / notifications payload 差異
    - copilot / agent tool result 穩定子集合
    - frontend mock cast 與 legacy-flexible 判定
  - 將 10.7 改為可選的最小護欄與自動化準備，不作為另一輪大重構
  - 補齊 docs 主要分類目錄的 README 規範入口，明確各目錄放置規則與維護邊界

---

二、frontend service 邊界清理

- 新增：
  - `frontend/src/services/knowledgeService.ts`
  - `frontend/src/services/__tests__/knowledgeService.test.ts`

- 調整：
  - 從 `frontend/src/services/timelineService.ts` 移除 `/knowledge/documents` 相關 API
  - `KnowledgeBaseView.vue` 改用 `knowledgeService`
  - `TimelineDetailDialog.vue` 的 project files 區塊改用 `knowledgeService`
  - `timelineService.test.ts` 移除 knowledge endpoint assertions
  - `KnowledgeBaseView.test.ts` 與 `TimelineDetailDialog.phase7.test.ts` 改 mock `knowledgeService`
  - `frontend/src/services/README.md` 補上 service 邊界說明

- 收斂結果：
  - timeline service 回到 timeline 主線
  - knowledge API 由個人知識庫與 Timeline project files 共用，但 frontend 入口改為獨立 service
  - 未改 backend API shape、knowledge 權限流程或 AI / RAG 流程

---

三、group snapshot 與 tool output 契約收斂

- 調整：
  - `backend/contracts/group_contracts.py`
    - 新增 group snapshot summary / digest / item named schema
    - `GroupSnapshotResponse.summary` 從 `dict[str, Any]` 改為 `GroupSnapshotSummaryResponse`
    - `GroupSnapshotJobResponse.snapshot` 改為 `GroupSnapshotResponse | None`
  - `backend/contracts/tool_outputs.py`
    - timeline AI generate tasks 改用 `TimelineGeneratedTaskResponse`
    - timeline conflict check 改用 `TimelineConflictCheckResponse`
    - timeline batch create tasks 改用 `TimelineBatchCreateTasksResponse`
    - group snapshot 改用 `GroupSnapshotResponse`
    - knowledge upload / list 改用 `KnowledgeDocumentUploadResponse`、`KnowledgeDocumentsListResponse`
    - task comment summary 改用 `TaskCommentSummaryPayloadResponse`

- 收斂結果：
  - 常用 tool result 不再以寬鬆 `dict[str, Any]` 描述已穩定 service response
  - tool envelope 外層仍維持 `{ ok, data }` / `{ ok, error }`
  - Copilot plan、trace metadata、planner intermediate data 仍保留 dynamic，不硬包成假穩定 schema

---

四、frontend fixture cast 與型別補正

- 調整：
  - `TimelineSubcomponents.test.ts`
    - 將純 fixture `as any` 改為 `satisfies` domain types
    - 補齊 task comment、knowledge event 等測試資料必要欄位
  - `frontend/src/types/timeline.ts`
    - `KnowledgeDocumentItem.chunk_count` 改為 `number | null`

- 收斂結果：
  - 測試資料不再靠過度寬鬆 cast 掩蓋 response shape
  - service mock cast 屬測試輔助型別，暫時保留
  - legacy-flexible list endpoint 短期保留，未來若統一 envelope 需另開 API 變更計畫

---

五、OpenAPI 與文件同步

- 重新匯出：
  - `docs/reference/openapi.json`

- 更新：
  - `docs/reference/Phase10_4_契約文件與OpenAPI維護整理_2026-06-18.md`
  - `docs/reference/Phase10_5_模組別主線導覽整理_2026-06-18.md`
  - `docs/重構計畫.md`
  - `docs/進度追蹤.md`
  - `docs/README.md`

- 同步內容：
  - 將 group snapshot 狀態更新為 summary 已收斂 named schema
  - 將常用 tool result 更新為已接上 named output model
  - 將 `knowledgeService.ts` 拆分結果回寫 10.5 / 10.6 文件
  - 記錄 timeline AI / RAG schema 判定為既有 named schema 足夠
  - 記錄 message REST / socket 維持共用 serializer
  - 記錄 legacy-flexible list endpoint 短期保留

---

六、驗證

- Backend focused tests：`30 passed`
  - 執行目錄：`backend/`
  - 指令：
    - `.\venv\Scripts\python.exe -m pytest tests\services\test_group_snapshot.py tests\blueprints\test_groups.py tests\services\test_tool_registry.py tests\services\test_response_contracts.py`
  - 備註：僅 `.pytest_cache` 權限 warning，不影響測試結果

- Frontend focused tests：`27 passed`
  - 執行目錄：`frontend/`
  - 指令：
    - `npm run test -- timelineService.test.ts knowledgeService.test.ts KnowledgeBaseView.test.ts TimelineDetailDialog.phase7.test.ts TimelineSubcomponents.test.ts`

- Frontend build：PASS
  - 執行目錄：`frontend/`
  - 指令：
    - `npm run build`
  - 備註：僅既有 chunk-size warning

- OpenAPI 靜態匯出：PASS
  - 執行目錄：`backend/`
  - 指令：
    - `.\venv\Scripts\python.exe scripts\export_openapi.py`
  - 輸出：
    - `docs/reference/openapi.json`

---

七、補充

- 這次提交完成 10.6 已知鬆動點清理，但不啟動新功能開發
- 10.7 目前維持可選，若後續不需要額外護欄，可直接銜接 Phase 11 integration tests 規劃
- 本輪保留 dynamic / binary / legacy-flexible 的正當性，不為了表面統一破壞既有 consumer
