# Backend 契約來源索引

> 更新日期：2026-06-17  
> 目的：快速指出 Learnlink 後端各主要模組的 request schema、response shape、guard、tool contract 與錯誤協議入口。  
> 注意：這份文件是索引，不是第二份真相；真正契約仍以 `backend/` 程式碼為主。

相關整理：

- `docs/reference/Phase10_2_後端契約收斂實作整理_2026-06-15.md`
- `docs/reference/Phase10_3_後端回應契約收斂實作整理_2026-06-17.md`

---

## 1. 全域共用入口

### 錯誤與驗證

- `backend/blueprints/validation.py`
  - `error_response`
  - `error_from_exception`
  - `validate_payload_or_400`

### 權限 guard

- `backend/blueprints/guards.py`
  - task / timeline member / owner guard

### contract / tool 基礎

- `backend/contracts/README.md`
- `backend/contracts/shared_fields.py`
- `backend/contracts/tool_inputs.py`
- `backend/contracts/tool_outputs.py`
- `backend/contracts/tool_envelopes.py`
- `backend/contracts/response_contracts.py`
- `backend/contracts/response_helpers.py`

### OpenAPI 輸出入口

- `backend/openapi_document.py`
- `/api/openapi.json`
- `/api/docs`
- `docs/reference/openapi.json`
- `backend/scripts/export_openapi.py`
  - 目前作為第一版閱讀與檢查入口
  - `/api/docs` 提供 Swagger UI 瀏覽介面
  - `docs/reference/openapi.json` 提供 repo 內固定輸出檔
  - 不取代 `backend/contracts/`、service payload 與測試作為真相來源

---

## 2. 模組索引

## 2.1 auth / profile

- request schema
  - `backend/blueprints/auth.py`
  - `backend/blueprints/profile.py`
  - `backend/contracts/auth_contracts.py`
  - `backend/contracts/profile_contracts.py`
- response shape
  - 固定成功回應：`backend/contracts/response_contracts.py`
  - 使用者資料 payload：`backend/services/auth_service.py`、`backend/services/profile_service.py`
- guard / auth context
  - `flask_jwt_extended`
- 備註
  - auth register 與 profile update/search request 已收斂到 `contracts/`
  - register / login / logout / refresh / profile update 固定回應已收斂到 `response_contracts.py`
  - auth current user / login nested user payload 已接上 `auth_contracts.py` 的 response model，並改為 schema 直接輸出
  - profile detail / search / chart-stats 已接上 `profile_contracts.py` 的 response model，並改為 schema 直接輸出

## 2.2 tasks

- request schema
  - `backend/blueprints/tasks.py`
  - `backend/contracts/task_contracts.py`
- response shape
  - `backend/blueprints/tasks.py`
  - `backend/services/task_service.py` 回傳 payload dict 的路徑
  - 固定 mutation response：`backend/contracts/response_contracts.py`
- guard
  - `backend/blueprints/guards.py`
- 備註
  - create/update/member/status 等 request schema 已收斂到 `task_contracts.py`
  - blueprint 主要保留 HTTP 錯誤映射與 route 邊界
  - create/update/delete/toggle/status/subtask/delete 類固定回應已收斂到 `response_contracts.py`
  - list/member/comment/file/subtask/AI summary 類 payload 由 `task_service.py` 承諾，並已接上 `task_contracts.py` 的 response model，主要 serializer 已改為 schema 直接輸出

## 2.3 timelines

- request schema
  - `backend/blueprints/timelines.py`
  - `backend/contracts/timeline_contracts.py`
- response shape
  - `backend/blueprints/timelines.py`
  - `backend/services/timeline_service.py`
  - 固定 mutation/search response：`backend/contracts/response_contracts.py`
- guard
  - `backend/blueprints/guards.py`
- 備註
  - create/update/remark/member/batch/conflict request schema 已集中到 `timeline_contracts.py`
  - service create/update 也已改用同目錄 contract 驗證
  - create/update/delete/remark/search user/remove member 固定回應已收斂到 `response_contracts.py`
  - timeline list / tasks / members / batch create / upcoming / member stats 已接上 `timeline_contracts.py` 的 response model，主要 serializer 已改為 schema 直接輸出
  - weekly report / risk analysis / conflict-check / AI generate / AI suggest plan 已補進 `timeline_contracts.py` 並改由 schema 輸出
  - `rag_planning_service.py` 的最終 payload 已接上 `TimelinePlanSuggestionResponse`

## 2.4 knowledge

- request schema
  - `backend/blueprints/knowledge.py`
  - `backend/contracts/knowledge_contracts.py`
- response shape
  - `backend/blueprints/knowledge.py`
  - `backend/services/knowledge_service.py`
- guard
  - blueprint 內 project-scoped permission 判斷
- 備註
  - batch document request 已收斂到 `knowledge_contracts.py`
  - upload/list/delete/reindex/batch/event JSON response 已接上 `knowledge_contracts.py` 的 response model，主要 serializer 已改為 schema 直接輸出
  - download / preview 屬 blob response，不硬塞入 JSON response contract

## 2.5 groups / notifications

- request schema
  - `backend/blueprints/groups.py`
  - `backend/blueprints/notifications.py`
  - `backend/contracts/group_contracts.py`
- response shape
  - 固定成功回應：`backend/contracts/response_contracts.py`
  - list / message / snapshot payload：`backend/services/group_service.py`
  - notification list payload：`backend/services/notification_service.py`
- guard
  - 群組 membership 邏輯在 blueprint + service
- 備註
  - create/join/message/snapshot request 已收斂到 `group_contracts.py`
  - group message 同時有 REST payload 與 socket event payload
  - group create/join/leave/send message/snapshot queued 與 notification counter/mutation 已收斂到 `response_contracts.py`
  - group list / members / messages / snapshot / snapshot job status 已接上 `group_contracts.py` 的 response model，主要 serializer 已改為 schema 直接輸出
  - notification list 已接上 `notification_contracts.py` 的 `NotificationResponse`，並改為 schema 直接輸出
  - message socket / REST 共用 serializer 已接上 `GroupRealtimeMessageResponse`，並改為 schema 直接輸出

## 2.6 todos / trash

- request schema
  - `backend/blueprints/todos.py`
  - `backend/contracts/todo_contracts.py`
- response shape
  - `backend/blueprints/todos.py`
  - `backend/blueprints/trash.py`
  - 固定 mutation response：`backend/contracts/response_contracts.py`
- guard
  - trash 以 service / auth context 為主
- 備註
  - create/update request 已收斂到 `todo_contracts.py`
  - todo create/update/delete/toggle 與 trash restore/delete 固定回應已收斂到 `response_contracts.py`
  - todo list 已接上 `todo_contracts.py` 的 `TodoResponse`，並改為 schema 直接輸出
  - trash list 已接上 `trash_contracts.py` 的 response model，並改為 schema 直接輸出

## 2.7 copilot / agent

- request schema
  - `backend/blueprints/copilot.py`
  - `backend/contracts/tool_inputs.py`
- response shape
  - `backend/blueprints/copilot.py`
  - `backend/services/copilot_service.py`
  - `backend/contracts/tool_outputs.py`
  - `backend/contracts/tool_envelopes.py`
  - tools list response：`backend/contracts/response_contracts.py`
- guard / protected fields
  - `backend/services/copilot_service.py`
  - `backend/chains/agent_nodes.py`
- 備註
  - 這塊目前最接近完整 contract 層，但仍混有 plan/trace/domain response
  - `/agent/tools` 已收斂到 `ToolsListResponse`
  - plan / execute / reject / replan 保留 agent 專用 payload，由 service 與 tool envelope 承諾

---

## 3. 後續使用方式

這份索引之後主要用在三個地方：

1. Phase 10.2
   - 判斷哪些模組要先收斂 request / response 主版本
2. Phase 10.3
   - 前端對齊時，快速找到對應後端真相來源
3. Phase 10.4
   - 若接 OpenAPI / Swagger，可從這份索引決定先接哪一層
