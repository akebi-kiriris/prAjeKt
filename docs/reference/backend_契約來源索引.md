# Backend 契約來源索引

> 更新日期：2026-06-12  
> 目的：快速指出 Learnlink 後端各主要模組的 request schema、response shape、guard、tool contract 與錯誤協議入口。  
> 注意：這份文件是索引，不是第二份真相；真正契約仍以 `backend/` 程式碼為主。

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

### service / tool contract 基礎

- `backend/services/contracts/README.md`
- `backend/services/contracts/tool_inputs.py`
- `backend/services/contracts/tool_outputs.py`
- `backend/services/contracts/tool_envelopes.py`

---

## 2. 模組索引

## 2.1 auth / profile

- request schema
  - `backend/blueprints/auth.py`
  - `backend/blueprints/profile.py`
- response shape
  - blueprint 內 `jsonify(...)`
- guard / auth context
  - `flask_jwt_extended`
- 備註
  - 目前以 blueprint payload 為主，尚未抽出獨立 service contract

## 2.2 tasks

- request schema
  - `backend/blueprints/tasks.py`
  - `backend/services/contracts/task_contracts.py`
- response shape
  - `backend/blueprints/tasks.py`
  - `backend/services/task_service.py` 回傳 payload dict 的路徑
- guard
  - `backend/blueprints/guards.py`
- 備註
  - 目前是 blueprint payload 與 service contract 雙軌並存

## 2.3 timelines

- request schema
  - `backend/blueprints/timelines.py`
  - `backend/services/contracts/timeline_contracts.py`
- response shape
  - `backend/blueprints/timelines.py`
  - `backend/services/timeline_service.py`
- guard
  - `backend/blueprints/guards.py`
- 備註
  - conflict-check / batch-create / weekly-report 已部分有 service contract

## 2.4 knowledge

- request schema
  - `backend/blueprints/knowledge.py`
- response shape
  - `backend/blueprints/knowledge.py`
  - `backend/services/knowledge_service.py`
- guard
  - blueprint 內 project-scoped permission 判斷
- 備註
  - 目前尚未看到獨立 domain contract 檔，之後可評估是否補

## 2.5 groups / notifications

- request schema
  - `backend/blueprints/groups.py`
  - `backend/blueprints/notifications.py`
- response shape
  - blueprint 直接 `jsonify(...)`
- guard
  - 群組 membership 邏輯在 blueprint + service
- 備註
  - group message 同時有 REST payload 與 socket event payload

## 2.6 todos / trash

- request schema
  - `backend/blueprints/todos.py`
- response shape
  - `backend/blueprints/todos.py`
  - `backend/blueprints/trash.py`
- guard
  - trash 以 service / auth context 為主
- 備註
  - 這塊相對穩定，可作為 mutation response 慣例參考

## 2.7 copilot / agent

- request schema
  - `backend/blueprints/copilot.py`
  - `backend/services/contracts/tool_inputs.py`
- response shape
  - `backend/blueprints/copilot.py`
  - `backend/services/copilot_service.py`
  - `backend/services/contracts/tool_outputs.py`
  - `backend/services/contracts/tool_envelopes.py`
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
