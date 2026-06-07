# API 端點總覽（Backend）

> Base URL（開發預設）：`http://localhost:5000/api`
>  
> 認證方式：JWT（`Authorization: Bearer <ACCESS_TOKEN>`）

---

## Auth

- `POST /api/auth/register`：註冊
- `POST /api/auth/login`：登入（access + refresh）
- `POST /api/auth/refresh`：刷新 access token

## Timelines

- `GET /api/timelines`：專案列表
- `POST /api/timelines`：建立專案
- `PUT /api/timelines/:id`：更新專案
- `DELETE /api/timelines/:id`：刪除專案
- `GET /api/timelines/:id/tasks`：專案任務明細
- `GET /api/timelines/:id/weekly-report`：週報
- `GET /api/timelines/:id/risk-analysis`：風險分析
- `POST /api/timelines/:id/risk-analysis/notify`：發送風險通知
- `POST /api/timelines/:id/conflict-check`：衝突檢查
- `POST /api/timelines/ai-suggest-plan`：RAG 規劃建議
- `POST /api/timelines/:id/generate-tasks`：AI 任務建議
- `POST /api/timelines/:id/batch-create-tasks`：批次建任務
- `GET /api/timelines/:id/members`：成員列表
- `POST /api/timelines/:id/members`：加入成員
- `DELETE /api/timelines/:id/members/:uid`：移除成員
- `POST /api/timelines/search_user`：搜尋可加入成員
- `GET /api/timelines/upcoming`：即將到期專案
- `GET /api/timelines/:id/member-stats`：成員統計

## Tasks

- `GET /api/tasks`：任務列表
- `GET /api/tasks/upcoming`：即將到期任務
- `POST /api/tasks`：建立任務
- `PUT /api/tasks/:id`：更新任務
- `DELETE /api/tasks/:id`：軟刪任務
- `PATCH /api/tasks/:id/status`：更新狀態
- `PATCH /api/tasks/:id/toggle`：切換完成
- `GET /api/tasks/:id/subtasks`：子任務列表
- `POST /api/tasks/:id/subtasks`：新增子任務
- `PATCH /api/tasks/:id/subtasks/:sid/toggle`：切換子任務完成
- `GET /api/tasks/:id/comments`：留言列表
- `POST /api/tasks/:id/comments`：新增留言
- `DELETE /api/tasks/:id/comments/:cid`：刪除留言
- `POST /api/tasks/:id/ai-comment-summary`：AI 留言摘要
- `GET /api/tasks/:id/files`：附件列表
- `POST /api/tasks/:id/upload`：上傳附件
- `GET /api/tasks/files/:filename`：下載/預覽附件
- `DELETE /api/tasks/:id/files/:fid`：刪除附件

## Groups

- `GET /api/groups`：群組列表
- `POST /api/groups`：建立群組
- `POST /api/groups/join`：邀請碼加入
- `POST /api/groups/:id/leave`：離開群組
- `GET /api/groups/:id/members`：群組成員
- `GET /api/groups/:id/messages`：訊息列表
- `POST /api/groups/:id/messages`：送訊息
- `POST /api/groups/:id/ai-snapshot`：生成群組快照
- `GET /api/groups/:id/ai-snapshot/latest`：最新快照
- `GET /api/groups/snapshot-jobs/:job_id`：快照工作狀態

## Knowledge

- `POST /api/knowledge/documents`：上傳並索引文件
- `GET /api/knowledge/documents`：文件列表（支援查詢/篩選/排序）
- `DELETE /api/knowledge/documents/:id`：刪除文件
- `POST /api/knowledge/documents/:id/reindex`：重建索引
- `POST /api/knowledge/documents/batch-delete`：批次刪除
- `POST /api/knowledge/documents/batch-reindex`：批次重建
- `GET /api/knowledge/documents/:id/download`：下載文件
- `GET /api/knowledge/documents/:id/preview`：預覽文件
- `GET /api/knowledge/documents/events`：操作事件

## Profile / Notification / Todo / Trash

- Profile
  - `GET /api/profile/me`
  - `PUT /api/profile/me`
  - `POST /api/profile/search`
  - `GET /api/profile/chart-stats`
- Notifications
  - `GET /api/notifications`
  - `GET /api/notifications/unread-count`
  - `PATCH /api/notifications/:id/read`
  - `PATCH /api/notifications/read-all`
- Todos
  - `CRUD /api/todos`
  - `PATCH /api/todos/:id/toggle`
- Trash
  - `GET /api/trash`
  - `PATCH /api/trash/tasks/:id/restore`
  - `DELETE /api/trash/tasks/:id`
  - `PATCH /api/trash/timelines/:id/restore`
  - `DELETE /api/trash/timelines/:id`

## Copilot Agent API（Phase 9.5）

- `POST /api/copilot/agent/plan`：建立可確認的執行計畫，回傳摘要、步驟預覽、風險提示、`proposal_source`、`proposal_reason`
- `POST /api/copilot/agent/execute`：僅執行已確認的 `plan_id`，不允許在 execute 階段覆寫參數
- `POST /api/copilot/agent/reject`：拒絕既有計畫
- `POST /api/copilot/agent/replan`：拒絕舊計畫後重新規劃，強制模型重提案並產生新 `plan_id`
- `GET /api/copilot/agent/tools`：取得目前已註冊工具清單與輸入 schema
- `POST /api/copilot/mcp/execute`：保留既有 MCP 路徑（相容舊流程）

---

## WebSocket（群組聊天室）

- `join-group`（Client -> Server）：加入群組房間
- `leave-group`（Client -> Server）：離開群組房間
- `send-message`（Client -> Server）：送出訊息
- `new-message`（Server -> Client）：同房間推播新訊息
- `error`（Server -> Client）：授權或參數錯誤
