# Phase 6 工作流

## 大綱

1. 範圍
2. 目前可用工作流
3. 執行備註

---

## 1) 範圍

此資料夾用於保存 Phase 6 AI 與 MCP 的操作流程文件。

目前範圍：

- RAG-A 任務留言摘要流程
- RAG-B 群組快照流程

---

## 2) 目前可用工作流

- `task-comment-summary.md`
- `group-snapshot.md`

---

## 3) 執行備註

- 工作流皆透過 `mcp_server.py` 呼叫既有後端 API。
- 提示詞與輸出格式需與後端契約保持一致。
- 只有在 API 契約穩定後才新增新流程檔。
