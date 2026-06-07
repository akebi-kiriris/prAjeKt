# Workflow：Task Comment Summary

## 目標

從任務留言歷史生成精簡且可執行的摘要。

## 輸入

- `task_id`（必填）

## MCP 工具

- `task_comment_summary(task_id)`

## 流程

1. 確認後端已啟動，且 MCP 認證環境變數設定完成。
2. 用有效 `task_id` 呼叫 MCP 工具。
3. 檢查輸出欄位：
- `summary.decisions`
- `summary.risks`
- `summary.next_actions`
4. 依 `docs/phase6-rag-evals.md`（RAG-A 表）記錄評分。

## 預期輸出

包含三個摘要陣列與 meta 資訊的 JSON payload。

## 失敗處理

- 若 403：確認呼叫者是否具備任務成員權限。
- 若 503：確認 AI provider 設定後再重試。
