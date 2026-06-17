# Phase 10.4 契約文件與 OpenAPI 維護整理

> 日期：2026-06-18  
> 範圍：閱讀版契約狀態矩陣、文件維護原則、OpenAPI 靜態匯出流程、OpenAPI 覆蓋與暫未覆蓋缺口清單。  
> 定位：本文件是 10.4 的閱讀與維護入口，不取代 `backend/contracts/`、route / service 實作、response contract、OpenAPI builder 或 focused tests 作為真相來源。

---

## 1. 真相來源與輸出層分工

Phase 10.4 只整理契約成果如何被查閱與維護，不重新定義 API。

目前分工如下：

1. `backend/contracts/`
   - 後端 request / response schema、tool input / output、共用欄位與 response helper 的主要真相來源
2. backend route / service
   - HTTP 邊界、權限檢查、流程判斷、service payload 與非 JSON response 的實際行為來源
3. backend focused tests
   - 契約 shape、OpenAPI path/schema ref、service serializer 與 blueprint 行為的驗證來源
4. `backend/openapi_document.py`
   - OpenAPI 文件產生邏輯
5. `/api/openapi.json`
   - runtime OpenAPI JSON 入口
6. `/api/docs`
   - Swagger UI 瀏覽入口
7. `docs/reference/openapi.json`
   - repo 內固定靜態輸出檔，供人工 review 與前後端對照
8. 本文件
   - 閱讀版狀態矩陣、缺口標記與維護流程入口

若文件與程式碼不同步，先回到 `backend/contracts/`、route / service、OpenAPI builder 或 tests 修正；不要只手動改文件讓它漂成另一套規格。

---

## 2. 契約狀態標記

閱讀版矩陣統一使用以下狀態：

| 狀態 | 意義 | 維護方式 |
| --- | --- | --- |
| `stable` | request schema、response contract、OpenAPI 與 focused tests 已有基本對齊 | 變更時視為契約變更，同步檢查 backend / frontend / OpenAPI / tests |
| `partial` | 主要外型已收斂，但仍有部分 payload 由 service / route 或歷史 shape 承諾 | 允許維持，但要在後續維護中逐步補強 |
| `dynamic` | payload 本質需要保留彈性，例如 agent/tool result、trace metadata、tool payloads | 如實標記，不硬包成假穩定 schema |
| `binary` | file download / preview 這類非 JSON response | OpenAPI 以 binary response 表示，不放進 JSON response contract |
| `legacy-flexible` | 為了維持既有 frontend shape 或歷史 API 相容性而保留的外型 | 保留原因要寫清楚，後續若改 shape 需當成 API 變更處理 |

---

## 3. 契約狀態矩陣

### 3.1 auth / profile

| API / 流程 | request schema | response contract | OpenAPI | focused tests | 狀態 | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
| `POST /auth/register` | `RegisterRequest` | `UserIdMutationResponse` | 已覆蓋 | 已覆蓋 | `stable` | 固定 mutation response |
| `POST /auth/login` | `LoginRequest` | `AuthLoginResponse` | 已覆蓋 | 已覆蓋 | `stable` | nested user 已接 `AuthUserResponse` |
| `POST /auth/logout` | 不適用 | `MessageResponse` | 已覆蓋 | 已覆蓋 | `stable` | auth context 由 JWT guard 決定 |
| `POST /auth/refresh` | 不適用 | `AuthRefreshResponse` | 已覆蓋 | 已覆蓋 | `stable` | frontend `api.ts` refresh typing 已收斂 |
| `GET /auth/me` | 不適用 | `CurrentUserResponse` | 已覆蓋 | 已覆蓋 | `stable` | frontend 不再直接 `as User` |
| `GET /profile/me` | 不適用 | `ProfileResponse` | 已覆蓋 | 已覆蓋 | `stable` | profile detail 已由 schema 輸出 |
| `PUT /profile/me` | `ProfileUpdateRequest` | `MessageResponse` | 已覆蓋 | 已覆蓋 | `stable` | 固定成功回應 |
| `POST /profile/search` | `ProfileSearchRequest` | `ProfileSearchResponse` | 已覆蓋 | 已覆蓋 | `stable` | search response 已 schema 化 |
| `GET /profile/chart-stats` | 不適用 | `ProfileChartStatsResponse` | 已覆蓋 | 已覆蓋 | `stable` | chart stats consumer 已移除多餘 cast |

### 3.2 tasks

| API / 流程 | request schema | response contract | OpenAPI | focused tests | 狀態 | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
| `GET /tasks` | query / route 邊界 | `TaskListItemResponse[]` | 已覆蓋 | 已覆蓋 | `legacy-flexible` | 維持既有裸陣列 shape，不改成 `{ data: [...] }` |
| `POST /tasks` | `TaskCreateRequest` | `TaskIdMutationResponse` | 已覆蓋 | 已覆蓋 | `stable` | mutation response 維持既有 `task_id` |
| `PUT /tasks/{task_id}` | `TaskUpdateRequest` | `MessageResponse` | 已覆蓋 | 已覆蓋 | `stable` | route-owned id 不由 frontend payload 自送 |
| `DELETE /tasks/{task_id}` | 不適用 | `MessageResponse` | 已覆蓋 | 已覆蓋 | `stable` | 固定成功回應 |
| `PATCH /tasks/{task_id}/toggle` | 不適用 | `CompletionResponse` | 已覆蓋 | 已覆蓋 | `stable` | `completed` shape 已固定 |
| `PATCH /tasks/{task_id}/status` | `TaskStatusRequest` | `TaskStatusMutationResponse` | 已覆蓋 | 已覆蓋 | `stable` | status mutation shape 已固定 |
| task members | `TaskMemberAddRequest` / `TaskMemberRoleUpdateRequest` | `TaskMemberResponse` / `MessageResponse` | 已覆蓋 | 已覆蓋 | `stable` | member role update / remove 已收斂 |
| task comments | `TaskCommentRequest` | `TaskCommentResponse` / `MessageResponse` | 已覆蓋 | 已覆蓋 | `stable` | AI summary 另有 payload response |
| task files / upload / download | multipart / route 邊界 | `TaskFileResponse` / `TaskFileUploadResponse` / binary | 已覆蓋 | 已覆蓋 | `partial` | upload/list/delete 已 schema 化；download 為 file response |
| subtasks | `SubtaskCreateRequest` / `SubtaskUpdateRequest` | `SubtaskResponse` / `SubtaskMutationResponse` | 已覆蓋 | 已覆蓋 | `stable` | list 維持既有 shape |
| `GET /tasks/upcoming` | 不適用 | task service payload | 已覆蓋 | 已覆蓋 | `legacy-flexible` | frontend 已以 `UpcomingTaskRaw[]` 對齊 |

### 3.3 timelines

| API / 流程 | request schema | response contract | OpenAPI | focused tests | 狀態 | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
| `GET /timelines` | query / route 邊界 | `TimelineListItemResponse[]` | 已覆蓋 | 已覆蓋 | `legacy-flexible` | 維持既有裸陣列 shape |
| `POST /timelines` | `TimelineCreateRequest` | `IdMutationResponse` | 已覆蓋 | 已覆蓋 | `stable` | 固定 mutation response |
| `PUT /timelines/{timeline_id}` | `TimelineUpdateRequest` | `MessageResponse` | 已覆蓋 | 已覆蓋 | `stable` | service input 已接 contract |
| `DELETE /timelines/{timeline_id}` | 不適用 | `MessageResponse` | 已覆蓋 | 已覆蓋 | `stable` | 固定成功回應 |
| `PUT /timelines/{timeline_id}/remark` | `TimelineRemarkRequest` | `MessageResponse` | 已覆蓋 | 已覆蓋 | `stable` | remark request 已集中 |
| timeline members | `TimelineAddMemberRequest` | `TimelineMemberResponse` / `MessageResponse` | 已覆蓋 | 已覆蓋 | `stable` | search user 使用 `SearchUserResponse` |
| timeline tasks | route 邊界 | `TimelineTaskItemResponse[]` | 已覆蓋 | 已覆蓋 | `legacy-flexible` | 保留既有 list shape |
| weekly report | 不適用 | `WeeklyReportResponse` | 已覆蓋 | 已覆蓋 | `stable` | OpenAPI test 已檢查 schema ref |
| risk analysis / notify | 不適用 | `TimelineRiskAnalysisResponse` / `TimelineRiskNotificationResponse` | 已覆蓋 | 已覆蓋 | `stable` | graph / summary / risk items 已 schema 化 |
| conflict check | `ConflictCheckInput` | `TimelineConflictCheckResponse` | 已覆蓋 | 已覆蓋 | `stable` | conflict payload 已 schema 化 |
| generate tasks / batch create | `TimelineGenerateTasksRequest` / `TimelineBatchCreateTasksRequest` | `TimelineGenerateTasksResponse` / `TimelineBatchCreateTasksResponse` | 已覆蓋 | 已覆蓋 | `stable` | AI generate 仍維持既有回傳 key |
| `POST /timelines/ai-suggest-plan` | request payload / route 邊界 | `TimelinePlanSuggestionResponse` | 已覆蓋 | 已覆蓋 | `stable` | `rag_planning_service.py` 已接 schema 輸出 |
| `GET /timelines/upcoming` | 不適用 | `UpcomingTimelineResponse` | 已覆蓋 | 已覆蓋 | `legacy-flexible` | frontend 已對齊 `UpcomingItem[]` |

### 3.4 knowledge

| API / 流程 | request schema | response contract | OpenAPI | focused tests | 狀態 | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
| `POST /knowledge/documents` | multipart / route 邊界 | `KnowledgeDocumentUploadResponse` | 已覆蓋 | 已覆蓋 | `stable` | upload response 已 schema 化 |
| `GET /knowledge/documents` | query / route 邊界 | `KnowledgeDocumentsListResponse` | 已覆蓋 | 已覆蓋 | `stable` | list response 已 schema 化 |
| `DELETE /knowledge/documents/{document_id}` | route 邊界 | `KnowledgeDocumentIdResponse` | 已覆蓋 | 已覆蓋 | `stable` | 固定 id response |
| `POST /knowledge/documents/{document_id}/reindex` | route 邊界 | `KnowledgeDocumentReindexResponse` | 已覆蓋 | 已覆蓋 | `stable` | reindex response 已 schema 化 |
| batch delete / reindex | `KnowledgeDocumentBatchRequest` | `KnowledgeBatchResponse` | 已覆蓋 | 已覆蓋 | `stable` | batch meta / items 已 schema 化 |
| `GET /knowledge/documents/events` | query / route 邊界 | `KnowledgeDocumentEventsResponse` | 已覆蓋 | 已覆蓋 | `stable` | event response 已 schema 化 |
| download / preview | 不適用 | binary response | 已覆蓋 | 已覆蓋 | `binary` | 非 JSON response，不放進 JSON contract |

### 3.5 groups / messages / notifications

| API / 流程 | request schema | response contract | OpenAPI | focused tests | 狀態 | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
| `GET /groups` | 不適用 | `GroupListItemResponse[]` | 已覆蓋 | 已覆蓋 | `legacy-flexible` | 維持既有 list shape |
| `POST /groups` | `GroupCreateRequest` | `GroupCreateResponse` | 已覆蓋 | 已覆蓋 | `stable` | invite code / group id shape 已固定 |
| `POST /groups/join` | `GroupJoinRequest` | `MessageResponse` | 已覆蓋 | 已覆蓋 | `stable` | join request 已 contract 化 |
| `POST /groups/{group_id}/leave` | 不適用 | `MessageResponse` | 已覆蓋 | 已覆蓋 | `stable` | membership 邏輯仍在 blueprint / service |
| group members | route 邊界 | `GroupMemberResponse[]` | 已覆蓋 | 已覆蓋 | `stable` | member response 已 schema 化 |
| group messages | `GroupMessageRequest` | `GroupMessageResponse` / `GroupMessageSentResponse` | 已覆蓋 | 已覆蓋 | `stable` | socket / REST serializer 已共用 response model |
| group AI snapshot | `GroupSnapshotRequest` | `GroupSnapshotQueuedResponse` / `GroupSnapshotResponse` / `GroupSnapshotJobResponse` | 已覆蓋 | 已覆蓋 | `partial` | snapshot `summary` 內容保留 dict 彈性 |
| messages unread / mark read | 不適用 | `UnreadCountResponse` / `MessageResponse` | 已覆蓋 | 已覆蓋 | `stable` | counter / mutation shape 已固定 |
| notifications list | 不適用 | `NotificationResponse[]` | 已覆蓋 | 已覆蓋 | `legacy-flexible` | list 維持既有 shape |
| notification counter / mutations | 不適用 | `CountResponse` / `MessageResponse` | 已覆蓋 | 已覆蓋 | `stable` | read / read-all / delete 已固定 |

### 3.6 todos / trash

| API / 流程 | request schema | response contract | OpenAPI | focused tests | 狀態 | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
| `GET /todos` | 不適用 | `TodoResponse[]` | 已覆蓋 | 已覆蓋 | `legacy-flexible` | list 維持既有 shape |
| `POST /todos` | `TodoCreateRequest` | `IdMutationResponse` | 已覆蓋 | 已覆蓋 | `stable` | fixed id response |
| `PUT /todos/{todo_id}` | `TodoUpdateRequest` | `MessageResponse` | 已覆蓋 | 已覆蓋 | `stable` | update request 已 contract 化 |
| `DELETE /todos/{todo_id}` | 不適用 | `MessageResponse` | 已覆蓋 | 已覆蓋 | `stable` | 固定成功回應 |
| `PATCH /todos/{todo_id}/toggle` | 不適用 | `CompletionResponse` | 已覆蓋 | 已覆蓋 | `stable` | completed shape 已固定 |
| `GET /trash` | 不適用 | `TrashPayloadResponse` | 已覆蓋 | 已覆蓋 | `stable` | task / timeline trash item 已 schema 化 |
| trash restore / delete | route 邊界 | `MessageResponse` | 已覆蓋 | 已覆蓋 | `stable` | restore / permanent delete shape 已固定 |

### 3.7 copilot / agent

| API / 流程 | request schema | response contract | OpenAPI | focused tests | 狀態 | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
| `GET /copilot/agent/tools` | 不適用 | `ToolsListResponse` | 已覆蓋 | 已覆蓋 | `stable` | frontend tool-list 外層型別已補齊 |
| `POST /copilot/agent/plan` | `CopilotAgentPlanRequest` | `CopilotGenericResponse` / service payload | 已覆蓋 | 已覆蓋 | `dynamic` | plan steps / tool payloads 仍保留彈性 |
| `POST /copilot/agent/execute` | `CopilotAgentExecuteRequest` | `CopilotGenericResponse` / tool envelope | 已覆蓋 | 已覆蓋 | `dynamic` | tool-specific result 不假裝穩定 |
| `POST /copilot/agent/reject` | `CopilotAgentRejectRequest` | `CopilotGenericResponse` | 已覆蓋 | 已覆蓋 | `dynamic` | agent 專用 payload |
| `POST /copilot/agent/replan` | `CopilotAgentReplanRequest` | `CopilotGenericResponse` | 已覆蓋 | 已覆蓋 | `dynamic` | replan payload 保留 tool-specific 彈性 |
| `POST /copilot/mcp/execute` | `CopilotMcpExecuteRequest` | `CopilotGenericResponse` | 已覆蓋 | 已覆蓋 | `dynamic` | result / metadata 用 JSON 彈性型別描述 |

### 3.8 health

| API / 流程 | request schema | response contract | OpenAPI | focused tests | 狀態 | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
| `GET /health` | 不適用 | `HealthResponse` | 已覆蓋 | OpenAPI focused test 間接守護 | `stable` | infrastructure endpoint，非主要業務 contract |

---

## 4. OpenAPI 覆蓋與缺口清單

### 4.1 已覆蓋

目前 `docs/reference/openapi.json` 已覆蓋：

1. auth / profile
2. tasks
3. timelines
4. knowledge
5. groups / messages / notifications
6. todos / trash
7. copilot / agent
8. health
9. bearer auth security scheme
10. multipart upload
11. binary download / preview response
12. 主要 requestBody / response schema ref

### 4.2 暫未完全 schema 化，但已標記

以下不是 10.4 要硬改的缺口，而是維護時要如實標記的彈性區：

1. `copilot / agent`
   - tool-specific `result`
   - trace metadata
   - `tool_payloads`
   - planner / execution step data
2. group snapshot
   - snapshot `summary` 內層內容保留 dict 彈性
3. 既有 list endpoint
   - 多數 list 仍維持裸陣列或既有 payload shape，不改成統一 envelope
4. file download / preview
   - 屬 binary response，不進 JSON response contract
5. 少數非核心 frontend 頁面或測試 mock cast
   - 已不屬 10.3 / 10.4 主線阻塞，後續維護遇到時再順手收斂

### 4.3 後續若要更進一步

後續若要再提高自動化，可以另開 10.6+ 或後續 phase 處理：

1. 從 Pydantic model 更自動地匯出 OpenAPI schema
2. 建立 OpenAPI 與 frontend type 的差異檢查
3. 逐步把 dynamic payload 中已穩定的內層 shape 拆成 named schema
4. 對所有 endpoint 做逐條差異表，而不是只用模組 / 流程矩陣

---

## 5. 文件維護原則

### 5.1 主從關係

1. 文件不是新的契約真相來源
2. 真相來源優先順序是：
   - `backend/contracts/`
   - route / service 實作
   - focused tests
   - `backend/openapi_document.py`
   - `docs/reference/openapi.json`
   - 閱讀版文件
3. 閱讀版文件應描述目前狀態，不手動創造尚未存在的 schema
4. dynamic / binary / legacy-flexible 狀態要明確寫出，不把它們誤算成漏做

### 5.2 何時要更新文件

以下情況需要更新本文件或相關 reference：

1. 新增主要 API
2. 修改主要 API request / response shape
3. 新增或移除 OpenAPI path
4. response model 從 service payload 升級為 schema 直接輸出
5. dynamic payload 中某段 shape 變成穩定 contract
6. binary / multipart 行為改變
7. frontend consumer 依賴的 response shape 有變更

以下情況通常不需要新增新文件，只需要更新矩陣或備註：

1. 純文件措辭修正
2. focused test 名稱或數量更新
3. 某 endpoint 從 `partial` 變成 `stable`
4. OpenAPI 缺口狀態變更

### 5.3 契約變更最小檢查清單

每次修改主要 API 時，至少檢查：

1. backend request schema
2. backend response contract / service payload
3. blueprint 是否仍只負責 HTTP 邊界與錯誤映射
4. frontend `types/`
5. frontend `services/`
6. store / component consumer 是否還有不必要 cast
7. `backend/openapi_document.py`
8. `docs/reference/openapi.json`
9. focused backend tests
10. focused frontend tests，如該 API 有主要 consumer

---

## 6. OpenAPI 維護流程

### 6.1 Runtime 與靜態檔關係

1. `/api/openapi.json`
   - Flask app runtime 產生的 OpenAPI JSON
2. `/api/docs`
   - Swagger UI 讀取 `/api/openapi.json`
3. `docs/reference/openapi.json`
   - 由匯出腳本產生的 repo 靜態檔
   - 用於 review、前後端對照與文件追蹤

### 6.2 匯出指令

從 `backend/` 目錄執行：

```powershell
.\venv\Scripts\python.exe scripts/export_openapi.py
```

預期輸出：

```text
docs/reference/openapi.json
```

### 6.3 匯出時機

以下情況應重新匯出：

1. 新增 / 移除 API path
2. 修改主要 request schema
3. 修改主要 response schema
4. 修改 security scheme
5. 修改 multipart / binary response 文件
6. dynamic payload 標記策略改變
7. `backend/openapi_document.py` 有任何 path / schema / component 修改

### 6.4 匯出後最低檢查

匯出後至少確認：

1. `docs/reference/openapi.json` 有被更新且仍是合法 JSON
2. `openapi` 版本仍是 `3.1.0`
3. `info.title` 仍是 `Learnlink Backend API`
4. 主要 path 仍存在：
   - `/tasks`
   - `/timelines/{timeline_id}/weekly-report`
   - `/knowledge/documents`
   - `/copilot/agent/tools`
5. 關鍵 schema ref 沒斷：
   - `TaskCreateRequest`
   - `WeeklyReportResponse`
   - `ToolsListResponse`
   - `ApiErrorResponse`
6. bearer auth security scheme 仍存在
7. multipart upload 與 binary download / preview 仍正確標記
8. `copilot / agent` dynamic payload 沒被誤標成 fully stable schema

### 6.5 建議驗證指令

從 `backend/` 目錄執行 OpenAPI focused tests：

```powershell
.\venv\Scripts\python.exe -m pytest tests/services/test_response_contracts.py -q
```

目前這組測試會守住：

1. response payload shape
2. unexpected field 禁止
3. OpenAPI primary path
4. request / response schema ref
5. bearer auth security scheme
6. OpenAPI 靜態匯出

---

## 7. 10.4 完成狀態

本輪完成後，Phase 10.4 的狀態可視為：

1. 閱讀版契約狀態矩陣已建立
2. OpenAPI 覆蓋與暫未完全 schema 化區塊已集中標記
3. 文件維護原則已明確寫出
4. OpenAPI runtime / static export 關係已寫清楚
5. 靜態匯出指令與 focused test 指令已固定
6. 後續若有契約變更，可按本文件檢查而不是重新盤點整個 Phase 10

### 驗證結果

1. OpenAPI 靜態匯出：PASS
   - 執行目錄：`backend/`
   - 指令：`.\venv\Scripts\python.exe scripts\export_openapi.py`
   - 輸出：`docs/reference/openapi.json`
   - 結果：匯出成功，靜態檔與目前 repo 內容無差異
2. OpenAPI focused tests：`6 passed`
   - 執行目錄：`backend/`
   - 指令：`.\venv\Scripts\python.exe -m pytest tests\services\test_response_contracts.py -q`
   - 備註：僅 `.pytest_cache` 權限 warning，不影響測試結果

---

## 8. 後續交接給 10.5 / 10.6 的項目

10.4 已完成文件與輸出層維護整理；後續若繼續進 10.5 / 10.6，建議聚焦：

1. 模組別主線導覽
   - 從頁面入口、frontend type、service、API、backend contract 串成閱讀路線
2. 真正高風險鬆動點
   - 只針對仍可能造成 runtime drift 的區塊，不重做本文件矩陣
3. dynamic payload 細化
   - 只在 `copilot / agent` 某些內層 shape 真的穩定後，再抽成 named schema
4. OpenAPI / frontend type 差異檢查
   - 若要更工程化，可另補自動化，不放在 10.4 內硬做
