# Phase 9.5：模型提案式 Plan（規則保留）與 Replan 強制二次確認

> 日期：2026-06-02  
> 目標：把 9.4 的雙階段流程升級為「模型提案為主、規則 fallback」且不放棄執行安全邊界。

---

## 1. 核心定位

9.4 已完成 `Plan -> Confirm -> Execute` 骨架。  
9.5 要解決的是：目前 `build_pending_tools` 純關鍵詞路由在複雜需求下彈性不足。

因此 9.5 採雙軌：

1. 模型提案主路徑（預設）
2. 規則路由 fallback（保留 `build_pending_tools`）

---

## 2. 設計原則（不變）

1. 提案權與執行權分離  
模型只能提案，不可直接調工具。

2. 使用者確認必經  
所有寫入類操作都必須 `confirm` 才可執行。

3. 安全欄位不可覆寫  
`user_id/actor_user_id/created_by/timeline_id/task_id/group_id` 仍由後端 context 決定。

---

## 3. 9.5 流程

1. `POST /copilot/agent/plan`
  - 準備 `tool list + docstring + input schema + side effects`
  - 模型輸出 `steps + payload_draft + reason`
  - 後端驗證（白名單 + schema + 依賴順序）
  - 驗證失敗時 fallback 規則路由，或回 ask_user

2. 使用者 Confirm / Reject
  - Confirm：執行核准快照
  - Reject：走 `replan`

3. `POST /copilot/agent/replan`
  - 強制重新餵 tool list 給模型重提案
  - 產生新 plan_id
  - 必須再次 confirm

---

## 4. 模型提案輸出契約（草案）

```json
{
  "supported": true,
  "steps": [
    "create_timeline_for_user",
    "generate_timeline_tasks_with_ai",
    "batch_create_tasks_for_timeline"
  ],
  "payload_draft": {
    "create_timeline_for_user": {"data": {"name": "agent測試"}},
    "batch_create_tasks_for_timeline": {"tasks": []}
  },
  "reason": "先建立專案，才能建立該專案的任務依賴"
}
```

驗證規則：

1. `steps` 全部必須在白名單
2. `payload_draft` 僅可包含該工具 schema 欄位
3. 敏感欄位由後端覆寫或忽略

---

## 5. 實作清單

1. 新增 `backend/services/tool_plan_service.py`
  - 責任：模型提案、JSON 解析、提案驗證

2. 調整 `backend/services/copilot_service.py`
  - `create_copilot_agent_plan` 改為先走模型提案，再 fallback 規則
  - `replan` 強制模型重提案，不沿用舊 steps

3. 調整 `backend/chains/agent_nodes.py`
  - `build_pending_tools` 保留，只當 fallback

4. 前端 `CopilotDock.vue`
  - 在 plan 區塊顯示「提案理由」與「fallback 來源」

---

## 6. 測試策略（9.5）

1. 規則命中測試：高信心關鍵詞直接命中
2. 模型提案命中測試：複雜語句可產生合理 steps
3. 非法提案防護：模型回傳未知工具時必須拒絕
4. replan 測試：拒絕後重提案會產生新 plan_id，且需二次確認

---

## 7. Done 定義

1. 複雜需求不再只靠關鍵詞規則
2. 模型提案結果可驗證、可審計、可拒絕
3. replan 一律重跑模型提案與二次確認
4. 安全邊界（敏感欄位、白名單、confirm）不退化

