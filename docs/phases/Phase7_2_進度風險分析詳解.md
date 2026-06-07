# Phase 7.2 進度風險分析詳解（實作版）

> 更新日期：2026-04-19  
> 範圍：Learnlink Phase 7.2（已落地版本）

---

## 📚 文件大綱

1. 這個階段在解什麼問題
2. 做完後可以實際做什麼
3. 範圍與非範圍
4. 整體架構與資料流
5. 資料模型與欄位設計
6. 後端如何實作（CPM + 風險計算）
7. API 契約與回傳格式
8. 前端如何呈現與互動
9. 通知機制（風險預警）
10. 錯誤與邊界降級策略
11. 驗證結果與測試覆蓋
12. 已知限制與可改善方向
13. 日常操作手冊（給 PM/開發）
14. 與 Phase 7.3 / Phase 8 的銜接

---

## 1) 這個階段在解什麼問題

Phase 7.2 的核心目的，是把排程管理從「看單一截止日」升級成「看依賴鏈與整體工期風險」。

具體要解的痛點：

- 任務互相依賴時，延誤影響常常太晚才被發現。
- 任務資料不完整（缺日期、缺依賴）時，系統容易算不出結果或出錯。
- 團隊缺少「可行動」的風險輸出（哪個任務最關鍵、延誤會影響幾天、該先做什麼）。

Phase 7.2 的策略是：

- 導入任務依賴欄位 `depends_on_task_ids`。
- 用 DAG/CPM 做關鍵路徑與浮時分析。
- 將資料異常轉為 `warnings`，避免直接 500。
- 在前端直接顯示風險摘要、關鍵路徑、風險任務、警示。

---

## 2) 做完後可以實際做什麼

現在系統可以直接做到：

- 任務可設定前置依賴（同專案、不可自依賴、去重）。
- 取得專案風險分析：
  - 關鍵路徑
  - 風險任務清單
  - 影響天數（impact days）
  - 資料警示（warnings）
- 在專案詳情視窗查看風險分析面板。
- 甘特圖依賴線改用真實 `depends_on_task_ids`（非舊版自動串接）。
- 由 API 手動觸發風險通知（owner 權限）。

實務效果：

- 更早發現阻塞任務與延誤傳導路徑。
- 排程討論不再只靠主觀判斷，能用欄位與計算結果對齊。
- 任務資料品質問題（循環、缺失、日期異常）會被明確提示，不會整包分析失敗。

---

## 3) 範圍與非範圍

本階段已包含：

- `task.depends_on_task_ids` 資料欄位與 migration。
- `critical_path_service.py` 風險分析引擎。
- `GET /api/timelines/{id}/risk-analysis`。
- `POST /api/timelines/{id}/risk-analysis/notify`（手動通知）。
- 前端風險分析 UI、依賴編輯 UI、甘特圖依賴改造。

本階段刻意不包含：

- ECharts 網狀圖可視化（列為選配，未阻塞 7.2 MVP）。
- 自動定時風險掃描（通知目前為手動/API 觸發）。

---

## 4) 整體架構與資料流

流程（高層）：

1. 使用者在任務建立/編輯時設定 `depends_on_task_ids`。
2. 後端驗證依賴合法性（型別、範圍、同專案、自依賴）。
3. 呼叫 risk-analysis API 時：
   - 讀取專案任務
   - 建立依賴圖（DiGraph）
   - 做 CPM 前推/後推
   - 產出 critical path、risk items、warnings、graph
4. 前端面板呈現摘要與明細。
5. 若需要，owner 可呼叫 notify API 送出風險預警通知。

---

## 5) 資料模型與欄位設計

### 任務欄位

- 欄位：`depends_on_task_ids`
- 類型：JSON（整數陣列）
- 規則：
  - 只允許正整數 ID
  - 自動去重
  - 不可包含自己
  - 必須為同專案任務

AI 任務生成補充（2026-04-20）：

- 生成預覽階段：AI 會優先輸出 `depends_on_task_refs`（以前置任務名稱表示）。
- 批次建立階段：後端會將 `depends_on_task_refs` 解析成正式 `depends_on_task_ids` 寫回任務。
- 若 AI 未提供依賴：系統會自動依生成順序補一條鏈（第 2 筆依第 1 筆、第 3 筆依第 2 筆...），避免全部為空。

### 設計理由

- MVP 先用 JSON 陣列降低 schema 複雜度。
- 後續若要做跨專案查詢或大規模分析，再考慮正規化依賴表。

---

## 6) 後端如何實作（CPM + 風險計算）

### 6.1 圖建立與資料清理

核心服務：`backend/services/critical_path_service.py`

做法：

- 先做依賴欄位 normalization。
- 過濾非法/缺失依賴並累積 warnings。
- 任務日期若不完整或無效，退化為 1 天工期並記錄 warnings。

### 6.2 循環依賴處理（降級策略）

- 使用 `networkx.is_directed_acyclic_graph` 檢查是否 DAG。
- 若有 cycle，會逐步移除 cycle 中一條邊，直到圖可計算。
- 會回傳：
  - `cycle_edge_removed`
  - `cycle_detected`

這表示「分析可繼續，但結果是降級近似值」。

### 6.3 CPM 計算

- Forward pass：計算 ES/EF。
- Backward pass：計算 LS/LF。
- Float 公式：$float = LS - ES$。
- 關鍵路徑：以最長工期路徑重建（DP + predecessor 回溯）。

### 6.4 風險判斷規則

任務未完成時，符合以下任一條件會進入 `risk_items`：

- 位於關鍵路徑（高風險）
- 已逾期（高風險，impact 至少為逾期天數）
- 非關鍵但浮時 <= 2 天（中風險）
- 日期不完整（中風險）

每個 risk item 都含：

- `severity`（high/medium/low）
- `impact_days`
- `reasons`
- `suggested_actions`
- `float_days`
- `depends_on_task_ids`

---

## 7) API 契約與回傳格式

### 7.1 取得風險分析

- Method: `GET`
- Path: `/api/timelines/{timeline_id}/risk-analysis`
- 權限：timeline member

主要回傳欄位：

```json
{
  "message": "風險分析完成",
  "timeline_id": 99,
  "timeline_name": "Phase7 專案",
  "generated_at": "2026-04-19T00:00:00Z",
  "summary": {
    "total_tasks": 6,
    "projected_duration_days": 18,
    "critical_path_task_count": 3,
    "critical_path_duration_days": 9,
    "risk_item_count": 2,
    "high_risk_count": 1,
    "warning_count": 1
  },
  "critical_path": [],
  "risk_items": [],
  "warnings": [],
  "graph": {
    "nodes": [],
    "edges": []
  }
}
```

### 7.2 手動觸發風險通知

- Method: `POST`
- Path: `/api/timelines/{timeline_id}/risk-analysis/notify`
- 權限：timeline owner

回傳摘要：

- `notified_user_count`
- `risk_item_count`
- `high_risk_count`
- `warning_count`

說明：

- 若無風險項目或專案無成員，不送通知，回傳對應訊息。
- 若有風險，會建立 `type = risk_alert` 的通知。

---

## 8) 前端如何呈現與互動

### 8.1 專案詳情視窗（TimelineDetailDialog）

已新增風險分析區塊：

- 摘要卡（預估總工期、關鍵路徑任務、高風險任務、警示數）
- 關鍵路徑列表
- 風險任務列表
- 資料警示列表
- 「產生依賴圖」按鈕：以 `riskAnalysis.graph.nodes/edges` 生成可視化依賴圖（可重新產生）

資料來源：`timelineService.getRiskAnalysis()`。

### 8.2 任務依賴編輯

已支援：

- 在 TimelineDetailDialog 新增任務時選依賴。
- 在 TasksView 編輯任務時選依賴。
- 送出前會做 id 正規化（轉整數、去重）。

### 8.3 甘特圖依賴

- 依賴來源改為任務實際 `depends_on_task_ids`。
- 只保留可渲染任務內的有效依賴。
- popup 顯示依賴任務名稱。

---

## 9) 通知機制（風險預警）

目前模式：手動/API 觸發。

通知內容：

- 標題：高風險數量或風險任務數量
- 內容：風險任務預覽 + 引導至風險面板
- 類型：`risk_alert`
- 連結：`/timelines`

注意：

- 目前前端尚未提供「一鍵觸發風險通知」按鈕（僅 API 可呼叫）。

---

## 10) 錯誤與邊界降級策略

Phase 7.2 的關鍵策略是「能算就算、不能算也要有提示」。

常見 warnings code：

- `invalid_dependency_format`
- `invalid_dependency_id`
- `self_dependency`
- `missing_dependency`
- `invalid_task_dates`
- `incomplete_schedule`
- `cycle_edge_removed`
- `cycle_detected`

效果：

- 避免因資料品質問題直接 500。
- 使用者可在 UI 看到可讀警示，進行資料修正。

---

## 11) 驗證結果與測試覆蓋

已驗證（2026-04-19）：

- 前端 targeted tests：12 passed
- 後端 targeted tests（7.2 關聯）：5 passed

覆蓋重點：

- 依賴欄位驗證（同專案、自依賴、去重）
- 風險分析 API 正常回傳 summary/warnings
- 循環依賴與缺失依賴降級
- 通知 API 權限（owner 可、member 不可）
- 前端 risk-analysis 介面渲染與 payload mapper 正規化

---

## 12) 已知限制與可改善方向

### P1（建議先做）

- 前端補上 notify API 按鈕與操作回饋（目前僅後端 API 有能力）。
- 通知加上冷卻/去重，避免短時間重複發送。

### P2（次要）

- 為 TimelineViewModes 的依賴轉換補專屬測試。
- 允許依賴候選包含已完成任務（可用灰色標示），提升歷史依賴建模完整性。

### P3（可延後）

- 引入使用者時區以優化逾期判斷邊界。
- 追加網狀圖視覺化（ECharts）提升依賴圖可讀性。

---

## 13) 日常操作手冊（給 PM/開發）

### 13.1 使用流程（產品視角）

1. 在任務建立/編輯時設定前置依賴。
2. 打開專案詳情，查看風險分析面板。
3. 先處理高風險任務與關鍵路徑任務。
4. 必要時由 owner 觸發風險通知給團隊。

AI 生成任務時的確認方式：

1. 在「AI 智能生成任務」視窗點選生成。
2. 在預覽卡片確認「🔗 前置」文字（此時是 `depends_on_task_refs`）。
3. 按「新增選取任務」後，回到任務詳情查看「前置依賴」或開啟編輯。
4. 重新整理後，應可看到任務的 `depends_on_task_ids` 已被寫入（至少第 2 筆起會有值）。

### 13.2 開發驗證（工程視角）

前端：

```bash
cd frontend
npm run test:run -- src/components/timelines/__tests__/TimelineDetailDialog.phase7.test.ts src/views/__tests__/TasksView.phase7.test.ts src/utils/__tests__/payloadMappers.test.ts src/services/__tests__/timelineService.test.ts
```

後端（venv）：

```bash
cd backend
.\venv\Scripts\python.exe -m pytest tests/services/test_services.py::test_task_service_validates_depends_on_task_ids tests/services/test_services.py::test_build_timeline_risk_analysis_detects_cycle_and_missing_dependency tests/services/test_services.py::test_trigger_timeline_risk_notifications_creates_notifications tests/blueprints/test_timelines.py::test_get_timeline_risk_analysis_returns_summary_and_warnings tests/blueprints/test_timelines.py::test_post_timeline_risk_analysis_notify_owner_only -q
```

---

## 14) 與 Phase 7.3 / Phase 8 的銜接

### 對 Phase 7.3 的價值

- `risk_items`、`critical_path`、`warnings` 可成為 AI 規劃建議的上下文來源。
- 未來可把高風險模式（例如常見阻塞鏈）餵給規劃助手做建議。

### 對 Phase 8 的價值

- 現有 notify API 可直接包成背景排程工作。
- 風險分析結果可封裝成 MCP 工具，提供外部自動化流程呼叫。

---

## ✅ 一句話總結

Phase 7.2 已把「任務依賴 + 關鍵路徑 + 風險預警」打通成可用 MVP：
不是只告訴你哪個任務晚了，而是告訴你「晚了會拖到哪裡、影響幾天、下一步先做什麼」。
