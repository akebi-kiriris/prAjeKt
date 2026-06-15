# Backend 契約來源索引

> 更新日期：2026-06-16  
> 目的：快速指出 Learnlink 後端各主要模組的 request schema、response shape、guard、tool contract 與錯誤協議入口。  
> 注意：這份文件是索引，不是第二份真相；真正契約仍以 `backend/` 程式碼為主。

相關整理：

- `docs/reference/Phase10_2_後端契約收斂實作整理_2026-06-15.md`

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

---

## 2. 模組索引

## 2.1 auth / profile

- request schema
  - `backend/blueprints/auth.py`
  - `backend/blueprints/profile.py`
  - `backend/contracts/auth_contracts.py`
  - `backend/contracts/profile_contracts.py`
- response shape
  - blueprint 內 `jsonify(...)`
- guard / auth context
  - `flask_jwt_extended`
- 備註
  - auth register 與 profile update/search request 已收斂到 `contracts/`
  - auth / profile response 仍主要由 blueprint 直接承諾

## 2.2 tasks

- request schema
  - `backend/blueprints/tasks.py`
  - `backend/contracts/task_contracts.py`
- response shape
  - `backend/blueprints/tasks.py`
  - `backend/services/task_service.py` 回傳 payload dict 的路徑
- guard
  - `backend/blueprints/guards.py`
- 備註
  - create/update/member/status 等 request schema 已收斂到 `task_contracts.py`
  - blueprint 主要保留 HTTP 錯誤映射與 route 邊界

## 2.3 timelines

- request schema
  - `backend/blueprints/timelines.py`
  - `backend/contracts/timeline_contracts.py`
- response shape
  - `backend/blueprints/timelines.py`
  - `backend/services/timeline_service.py`
- guard
  - `backend/blueprints/guards.py`
- 備註
  - create/update/remark/member/batch/conflict request schema 已集中到 `timeline_contracts.py`
  - service create/update 也已改用同目錄 contract 驗證

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
  - upload/list/delete 主線仍以 blueprint + service 邊界為主

## 2.5 groups / notifications

- request schema
  - `backend/blueprints/groups.py`
  - `backend/blueprints/notifications.py`
  - `backend/contracts/group_contracts.py`
- response shape
  - blueprint 直接 `jsonify(...)`
- guard
  - 群組 membership 邏輯在 blueprint + service
- 備註
  - create/join/message/snapshot request 已收斂到 `group_contracts.py`
  - group message 同時有 REST payload 與 socket event payload

## 2.6 todos / trash

- request schema
  - `backend/blueprints/todos.py`
  - `backend/contracts/todo_contracts.py`
- response shape
  - `backend/blueprints/todos.py`
  - `backend/blueprints/trash.py`
- guard
  - trash 以 service / auth context 為主
- 備註
  - create/update request 已收斂到 `todo_contracts.py`
  - 這塊相對穩定，可作為 mutation response 慣例參考

## 2.7 copilot / agent

- request schema
  - `backend/blueprints/copilot.py`
  - `backend/contracts/tool_inputs.py`
- response shape
  - `backend/blueprints/copilot.py`
  - `backend/services/copilot_service.py`
  - `backend/contracts/tool_outputs.py`
  - `backend/contracts/tool_envelopes.py`
- guard / protected fields
  - `backend/services/copilot_service.py`
  - `backend/chains/agent_nodes.py`
- 備註
  - 這塊目前最接近完整 contract 層，但仍混有 plan/trace/domain response

---

## 3. 後續使用方式

這份索引之後主要用在三個地方：

1. Phase 10.2
   - 判斷哪些模組要先收斂 request / response 主版本
2. Phase 10.3
   - 前端對齊時，快速找到對應後端真相來源
3. Phase 10.4
   - 若接 OpenAPI / Swagger，可從這份索引決定先接哪一層
