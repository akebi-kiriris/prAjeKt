# Phase 9.2 Tool Schema Contracts（執行版）

> 目的：固定 agent 調用契約，避免回傳形狀漂移（`int` / `dict` 混用）。  
> 原則：每個 tool 必須有 `InputSchema`、`SuccessSchema`、`ErrorSchema`。

---

## 統一 Envelope（9.3 實作目標）

### Success Envelope

```json
{
  "ok": true,
  "data": {}
}
```

### Error Envelope

```json
{
  "ok": false,
  "error": {
    "error_code": "VALIDATION_ERROR",
    "message": "欄位格式錯誤",
    "retryable": false,
    "hint": "請修正必填欄位後再試"
  }
}
```

---

## 契約對照（第一批工具）

| tool_name | InputSchema（現況/目標） | SuccessSchema（目標） | ErrorSchema | 現況差異 |
|---|---|---|---|---|
| `create_task_for_user` | `TaskCreateInput` + `assignee_user_ids/depends_on_task_ids` | `TaskCreateToolSuccess{task_id:int}` | `ToolError` | 現況主要回 `int` |
| `update_task_for_member` | `TaskUpdateInput` | `CommonToolSuccess{updated:bool}` | `ToolError` | 現況多為 `None` |
| `list_tasks_for_user` | `ListTasksToolInput{user_id:int}` | `ListTasksToolSuccess{tasks:list[TaskItem]}` | `ToolError` | 現況已為 list dict |
| `summarize_task_comments_for_member` | `TaskCommentSummaryToolInput{task_id:int}` | `TaskCommentSummaryToolSuccess` | `ToolError` | 已近似，需 envelope |
| `generate_timeline_tasks_with_ai` | `TimelineGenerateTasksInput`（既有） | `TimelineGenerateTasksToolSuccess` | `ToolError` | 需補統一錯誤碼 |
| `check_timeline_task_conflicts` | `ConflictCheckInput`（既有） | `TimelineConflictCheckToolSuccess` | `ToolError` | 需 envelope |
| `generate_group_snapshot` | `GroupSnapshotToolInput`（待補） | `GroupSnapshotToolSuccess` | `ToolError` | 可能同步/非同步雙模式 |
| `upload_and_index_knowledge_document` | `KnowledgeUploadToolInput`（待補） | `KnowledgeUploadToolSuccess` | `ToolError` | 目前依 Flask 檔案物件 |
| `list_knowledge_documents` | `KnowledgeListToolInput`（待補） | `KnowledgeListToolSuccess` | `ToolError` | 需明確 `meta` 結構 |

---

## 已存在可復用的 Pydantic 契約

1. `services/contracts/task_contracts.py`
   - `TaskCreateInput`
   - `TaskUpdateInput`
   - `TaskStatusUpdateInput`
2. `services/contracts/timeline_contracts.py`
   - `ConflictCheckInput`
   - `TimelineBatchCreateTasksInput`
   - `WeeklyReportInput`

---

## 9.3 新增模型建議

1. `backend/services/contracts/tool_envelopes.py`
   - `ToolError`
   - `ToolSuccess[T]`
   - `ToolResult[T]`（union）
2. `backend/services/contracts/tool_inputs.py`
   - `ListTasksToolInput`
   - `TaskCommentSummaryToolInput`
   - `GroupSnapshotToolInput`
   - `KnowledgeListToolInput`
3. `backend/services/contracts/tool_outputs.py`
   - `TaskCreateToolSuccess`
   - `CommonToolSuccess`
   - `TimelineGenerateTasksToolSuccess`
   - `KnowledgeListToolSuccess`

---

## 命名與穩定性規範

1. 欄位名稱固定使用 snake_case。
2. enum 欄位（`status`/`role`/`event_type`）盡量限制值域。
3. 同一 tool 不可同時回傳 primitive 與 object。
4. schema 變更需版本化或提供相容層（避免 graph node 綁壞）。
