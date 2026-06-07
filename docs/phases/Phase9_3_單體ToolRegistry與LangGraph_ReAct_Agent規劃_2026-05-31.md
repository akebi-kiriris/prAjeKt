# Phase 9.3：單體 Tool Registry 與 LangGraph ReAct Agent 規劃

> 日期：2026-05-31  
> 階段定位：Phase 9 第三階段（將 9.2 契約文件實作為可執行 agent 流程）  
> 前置條件：Phase 9.1（Type Hints）與 9.2（Docstring + 契約文件）已完成

---

## 目標

1. 建立單體後端版 tool registry（先不走 MCP），只暴露穩定高語意入口。
2. 將 tool registry 接入 LangGraph，實作 ReAct 迴圈（plan -> act -> observe -> re-plan）。
3. 讓系統可根據使用者輸入目的，循序呼叫多個函式完成任務。
4. 統一 tool I/O 契約（Pydantic + envelope）與錯誤路由（`error_code -> retryable -> route`）。

---

## 非目標（本階段不做）

1. 不重構核心業務邏輯（service 內部流程僅做最小調整）。
2. 不導入多服務拆分架構（route/service/realtime 多 server 先不做）。
3. 不把所有函式一次全部 tool 化（先完成第一批高價值入口）。
4. 不把 MCP 當主線（MCP 保留 backlog，日後再補）。

---

## 參考依據（9.2 產出）

1. `docs/phases/phase9_2_tool_entrypoints.md`
2. `docs/phases/phase9_2_tool_schema_contracts.md`
3. `docs/phases/phase9_2_error_semantics_matrix.md`
4. `重構計畫.md` 的 9.3 定義

---

## 9.3 交付定義（Done）

1. 後端存在可運行的 `tool registry`，且僅白名單暴露函式。
2. LangGraph 能完成至少 3 條多步 ReAct 流程（每條 >=2 次工具調用）。
3. 第一批工具完成統一 envelope：
   - 成功：`{ ok: true, data: ... }`
   - 失敗：`{ ok: false, error: { error_code, message, retryable, hint } }`
4. 錯誤可依矩陣路由到 `retry / ask_user / stop`。
5. 有 smoke tests 驗證：
   - 工具註冊完整性
   - 契約輸入輸出一致性
   - ReAct 最小閉環可跑通

---

## 實作範圍

## 第一批工具（必做）

1. `create_task_for_user`
2. `update_task_for_member`
3. `list_tasks_for_user`
4. `generate_timeline_tasks_with_ai`
5. `check_timeline_task_conflicts`
6. `generate_group_snapshot`
7. `upload_and_index_knowledge_document`
8. `list_knowledge_documents`
9. `summarize_task_comments_for_member`

## 第二批工具（可選）

1. `add_timeline_member_for_owner`
2. `build_weekly_report_for_timeline`
3. `create_group_for_user` / `join_group_by_invite_code`
4. `update_profile_for_user`

---

## 架構設計（單體版）

## A. Tool Registry 層

建議新增：

1. `backend/services/tools/registry.py`
2. `backend/services/tools/handlers.py`
3. `backend/services/contracts/tool_envelopes.py`
4. `backend/services/contracts/tool_inputs.py`
5. `backend/services/contracts/tool_outputs.py`
6. `backend/services/tools/error_mapper.py`

責任分工：

1. `registry.py`：註冊工具白名單與 metadata。
2. `handlers.py`：將 schema 驗證後的輸入轉調 service 函式。
3. `tool_envelopes.py`：統一定義 success/error 輸出型別。
4. `error_mapper.py`：將 `OperationError(status_code)` 映射到 `error_code/retryable/hint`。

## B. LangGraph Agent 層

建議新增：

1. `backend/chains/agent_state.py`
2. `backend/chains/agent_nodes.py`
3. `backend/chains/agent_graph.py`

最小圖節點：

1. `intent_parse_node`：解析使用者目標與上下文缺口。
2. `tool_select_node`：依目標與 state 決定下一個工具。
3. `tool_execute_node`：執行 registry 工具並寫入 observation。
4. `route_by_error_node`：依 `retryable/error_code` 路由。
5. `finalize_node`：整理最終回覆與步驟摘要。

---

## ReAct 循環規則（本專案版本）

1. 先規劃一個「下一步工具」而非整個長計畫。
2. 每次執行後將結果寫回 state（含成功/失敗與可重試資訊）。
3. 成功時進入下一輪選工具；失敗時依 error matrix 分支。
4. 設定最大循環次數（建議 6）避免無限迴圈。
5. 若缺關鍵參數，路由到 `ask_user` 結點主動追問。

---

## 錯誤路由實作規則

依 `docs/phases/phase9_2_error_semantics_matrix.md`：

1. `retryable=true` -> `retry node`（退避重試，上限 2~3 次）
2. `VALIDATION_ERROR/NOT_FOUND/CONFLICT` -> `ask_user node`
3. `PERMISSION_DENIED/INTERNAL_ERROR` -> `stop node`
4. `UPSTREAM_TIMEOUT/UPSTREAM_UNAVAILABLE` -> `retry`，超限後 `stop`

---

## 逐步執行計畫

## Step 1：契約骨架落地

1. 新增 `tool_envelopes.py`（`ToolError`、`ToolSuccess`、`ToolResult`）。
2. 依第一批工具建立 `tool_inputs.py` / `tool_outputs.py`。
3. 實作 `error_mapper.py`（status_code -> error_code）。

## Step 2：Registry 與 Handler

1. 實作工具註冊白名單（名稱、描述、input model、handler）。
2. 每個 handler 完成：
   - input schema 驗證
   - service 呼叫
   - success/error envelope 包裝
3. 禁止直接暴露 internal/helper。

## Step 3：LangGraph 最小閉環

1. 建立 agent state（目標、上下文、steps、last_error、final_answer）。
2. 串接 `tool_select -> tool_execute -> route` 循環。
3. 實作 `ask_user` 與 `stop` 輸出格式。

## Step 4：Smoke 測試

1. 工具註冊檢查：白名單工具可列舉與可調用。
2. 契約檢查：每個工具輸入錯誤時返回標準 `ToolError`。
3. ReAct 檢查：至少三個 scenario 跑通。

---

## 建議 Smoke Scenarios

1. 「幫我建立一個新任務並指派給某人」
   - 預期：`create_task_for_user` + （可選）`update_task_for_member`
2. 「幫我看這個專案有哪些衝突，順便給我建議」
   - 預期：`check_timeline_task_conflicts`（必要時走 AI）
3. 「幫我把最近任務留言整理成重點」
   - 預期：`summarize_task_comments_for_member`

---

## 風險與對策

1. 風險：工具回傳形狀不一致導致 graph node 崩潰。  
   對策：所有 handler 強制 envelope 包裝。

2. 風險：agent 誤選低階工具。  
   對策：只暴露白名單；`_` helper 不註冊。

3. 風險：外部 AI 不穩定造成循環卡住。  
   對策：timeout + retry 次數上限 + fallback stop 訊息。

4. 風險：授權資訊不足造成多輪失敗。  
   對策：優先在 `intent_parse` 補齊前置條件追問。

---

## MCP Backlog（保留未做）

- [ ] 將單體 registry 抽象成 MCP-compatible adapter
- [ ] 既有 `mcp_bridge_service` 與新 registry 做兼容映射
- [ ] 加入遠端工具發現與權限代理策略

---

## 提交策略（建議）

1. Commit A：tool contract models + error mapper
2. Commit B：registry + handlers（第一批工具）
3. Commit C：LangGraph graph + nodes（最小閉環）
4. Commit D：smoke tests + docs/進度同步
