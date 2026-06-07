# Phase 6 MCP 工具說明

## 大綱

1. 概覽
2. Server 入口
3. 認證模式
4. 工具清單
5. Gemini API 調用方式
6. 錯誤處理
7. 限制與備註

---

## 1) 概覽

Phase 6.5 目前開放兩個 MCP 工具，皆對應既有後端 API：

- `task_comment_summary(task_id)` -> RAG-A
- `group_snapshot(group_id, ...)` -> RAG-B

定位補充：MCP 是「外部 AI 主機」入口，不是前端入口；前端仍維持呼叫既有 REST API。

`weekly_review(user_id, week)` 尚未實作（待 6.4 完成）。

---

## 2) Server 入口

檔案：

- `mcp_server.py`

啟動：

```powershell
python mcp_server.py
```

若沒有 MCP 主機，可直接啟動：

```powershell
scripts\dev\start_mcp_inspector.bat
```

傳輸：

- stdio（FastMCP 預設）

---

## 3) 認證模式

擇一設定即可：

1. Token 模式

```env
PRAJEKT_ACCESS_TOKEN=<access-token>
```

2. 帳密模式

```env
PRAJEKT_EMAIL=<email>
PRAJEKT_PASSWORD=<password>
```

共用設定：

```env
PRAJEKT_API_BASE_URL=http://127.0.0.1:5000/api
PRAJEKT_TIMEOUT_SEC=30
```

---

## 4) 工具清單

### 4.1 `task_comment_summary(task_id)`

後端映射：

- `POST /api/tasks/{task_id}/ai-comment-summary`

輸入：

- `task_id`（int，必填）

輸出（範例）：

```json
{
  "task_id": 42,
  "summary": {
    "decisions": ["..."],
    "risks": ["..."],
    "next_actions": ["..."]
  },
  "meta": {
    "comment_count": 5,
    "provider": "gemini"
  }
}
```

### 4.2 `group_snapshot(group_id, window_days=30, async_mode=false, wait_for_job=true, poll_interval_sec=1.5, timeout_sec=90)`

後端映射：

- `POST /api/groups/{group_id}/ai-snapshot`
- `GET /api/groups/snapshot-jobs/{job_id}`（非同步）
- `GET /api/groups/{group_id}/ai-snapshot/latest`（fallback）

必要輸入：

- `group_id`（int）

可選輸入：

- `window_days`（int，預設 30）
- `async_mode`（bool，預設 false）
- `wait_for_job`（bool，預設 true）
- `poll_interval_sec`（float，預設 1.5）
- `timeout_sec`（int，預設 90）

輸出型態：

1. 同步完成：

```json
{
  "mode": "sync",
  "status": "completed",
  "result": {
    "snapshot_id": 7,
    "group_id": 3,
    "summary": {
      "digest": {
        "overview": "...",
        "todo_for_user": [],
        "watch_out": [],
        "decisions_brief": []
      }
    }
  }
}
```

2. 非同步排隊中：

```json
{
  "mode": "async",
  "status": "queued",
  "job": {
    "job_id": "...",
    "status": "queued"
  }
}
```

3. 非同步輪詢完成：

```json
{
  "mode": "async",
  "status": "completed",
  "job": {
    "job_id": "...",
    "status": "completed"
  },
  "result": {
    "snapshot_id": 8,
    "group_id": 3
  }
}
```

---

## 5) Gemini API 調用方式

可以調用，且目前已透過既有後端路徑生效：

1. MCP 工具呼叫後端 API
2. 後端讀取 `AI_PROVIDER=gemini`
3. 由 `services/ai_provider.py` 呼叫 Gemini API

這樣可以維持既有權限、錯誤處理與資料契約，不會分裂兩套 AI 邏輯。

---

## 6) 錯誤處理

MCP 工具會把後端錯誤轉成執行期錯誤拋出。

常見狀況：

- 400：輸入無效，或時間窗內無可摘要資料
- 401：Token 失效／認證錯誤
- 403：目前使用者不在目標 task/group 權限範圍
- 503：AI provider 暫時不可用

---

## 7) 限制與備註

- 目前工具是 wrapper，不複製後端商業邏輯。
- 權限仍由既有 backend API 強制驗證。
- 大量群聊建議使用 `async_mode=true`。
