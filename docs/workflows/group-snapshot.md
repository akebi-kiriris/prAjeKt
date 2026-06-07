# Workflow：Group Snapshot

## 目標

從近期群組訊息生成行動導向的摘要 Digest。

## 輸入

- `group_id`（必填）
- `window_days`（可選，預設 30）
- `async_mode`（可選，預設 false）

## MCP 工具

- `group_snapshot(group_id, window_days=30, async_mode=false, wait_for_job=true, poll_interval_sec=1.5, timeout_sec=90)`

## 流程

1. 確認後端已啟動，且 MCP 認證設定完成。
2. 小型群組先用同步模式呼叫。
3. 大量訊息群組改用 `async_mode=true`。
4. 非同步模式下持續查 job，直到 completed 或 timeout。
5. 驗證 Digest 欄位：
- `summary.digest.overview`
- `summary.digest.todo_for_user`
- `summary.digest.watch_out`
- `summary.digest.decisions_brief`
6. 依 `docs/phase6-rag-evals.md`（RAG-B 表）記錄評分。

## 預期輸出

回傳包含快照中繼資料與 digest 優先摘要的 JSON payload。

## 失敗處理

- 若 400 且無來源訊息：放寬日期範圍或先增加群組活動。
- 若 403：確認呼叫者是否為群組成員。
- 若 timeout：稍後查 latest snapshot。
