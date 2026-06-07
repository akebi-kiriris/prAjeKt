# Phase 7 精簡執行版（2026/04/22 校正版）

> **策略**：聚焦降低延期風險與週報成本，分階段精簡交付，避免功能膨脹。  
> **基線**：基於 Phase 6.6+ 既有 LangChain/LangGraph 架構，僅做最小必要擴展。  
> **時程**：大約 4-6 週（7.1/7.2/7.3 各 1-2 週）

---

## 📌 核心目標（只留兩項）

1. **降低延期風險**：專案/任務早期發現衝突與風險。
2. **降低週報成本**：一鍵生成可直接用的週報，減少手工整理時間。

---

## 🔄 現況校正（2026/04/22）

- Phase 7.1 核心能力已在現有程式碼落地：`completed_at`、`weekly-report` / `conflict-check` API、前端週報預覽與衝突預檢。
- 目前採 `services/timeline_service.py` 集中實作週報與衝突邏輯；若後續模組膨脹，再拆成獨立 service。
- `networkx`、`frappe-gantt`、`echarts` 已在專案依賴中，可直接進入 Phase 7.2。
- Phase 7.2 開工重點：補齊任務依賴欄位 + CPM 風險分析 + 風險視覺化。

---

## 📋 三個階段劃分

### 🟡 Phase 7.1：週報 + 衝突檢查 MVP（1-2 週）

**目的**：快速驗證「週報自動化」與「衝突提示」是否有實際價值。

**完成狀態（對齊現況）**：

**後端**：
- [ ] `task` 模型新增 `completed_at` 欄位（timestamp，可為 null）
- [ ] 新增 migration（`add_completed_at_to_task.py`）
- [ ] 新增 `services/weekly_report_service.py`（聚合已完成任務、留言、提交內容）
- [ ] 新增 `services/resource_conflict_service.py`（檢查人員/日期衝突）
- [ ] `blueprints/timelines.py` 新增兩個 API：
  - `GET /api/timelines/{timeline_id}/weekly-report?start_date=...&end_date=...`
  - `POST /api/timelines/{timeline_id}/conflict-check` （提交新任務，回傳衝突提示）

**前端**：
- [ ] `frontend/src/types/` 新增 `WeeklyReport` 與 `ResourceConflict` 型別
- [ ] `frontend/src/services/timelineService.ts` 新增兩個 API 呼叫
- [ ] `TimelinesView.vue` 或新增輔助 view（顯示衝突提示與週報預覽）
- [ ] 任務建立/編輯流程加上「衝突預檢」

**測試**：
- [x] 後端 service 與 blueprint 測試已覆蓋（衝突檢查邏輯、週報聚合邏輯）
- [x] 前端 service 測試已覆蓋 weekly-report / conflict-check 呼叫
- [ ] 前端 UI 互動測試（衝突提示顯示、週報列表）仍建議補強

**驗收條件**：
- ✅ 前端能看到週報內容（包含完成任務、進度率、風險標記）
- ✅ 前端建立任務時，系統提示衝突人員/日期
- ✅ 使用者可選擇接受/忽略衝突，流程正常
- ✅ 後端與前端測試各通過，無回歸

**時程建議**：
| 項目 | 人力日 | 備註 |
|------|---------|------|
| 後端 migration + service | 2 | 週報邏輯相對直接 |
| 後端 blueprint | 1 | 標準 GET/POST 包裝 |
| 前端型別與 service 層 | 1 | |
| 前端 UI 與整合 | 2 | 需驗證 UX |
| 測試 | 1.5 | |
| **合計** | **~7.5** | 1 週左右 |

---

### 🟡 Phase 7.2：進度風險分析 MVP（1-2 週）

**目的**：識別「關鍵路徑任務」與可能延期的 impact。

**詳細說明**：見 [Phase7_2_進度風險分析詳解.md](Phase7_2_進度風險分析詳解.md)。

**必要條件**：Phase 7.1 已驗收通過。

**執行決策（開工前定稿）**：

1. **依賴資料結構**：`task.depends_on_task_ids` 採 JSON 整數陣列（同專案任務 ID、不可重複、不可依賴自己）。
2. **CPM 邊界策略**：循環依賴/缺失依賴/日期不完整時不回 500，改回傳 `warnings` 並提供可讀提示。
3. **前端視覺化策略**：先用既有甘特圖做 7.2 MVP（依賴線 + 關鍵路徑高亮），網狀圖列為選配。

**需要的改動**：

**後端**：
- [x] `task` 模型新增 `depends_on_task_ids` 欄位（JSON array，先不正規化表）
- [x] 新增 migration（`add_depends_on_to_task.py`）
- [x] 新增 `services/critical_path_service.py`（DAG/CPM 計算，借助 `networkx` 套件）
- [x] `risk-analysis` payload 需含 `critical_path`、`risk_items`、`impact_days`、`warnings`
- [x] `blueprints/timelines.py` 新增 API：
  - `GET /api/timelines/{timeline_id}/risk-analysis` （回傳 critical path 與風險項目）
- [x] 補強通知系統（風險項目可觸發「風險預警」通知，先手動/API 觸發）

**前端**：
- [x] `frontend/src/types/` 新增 `CriticalPathAnalysis`、`RiskItem`、`RiskWarning` 型別
- [x] `frontend/src/services/timelineService.ts` 新增 `getRiskAnalysis()`
- [x] `TimelineDetailDialog.vue` 或新增分析面板（顯示 critical path、risk flags、建議動作）
- [x] 任務編輯時可設定「依賴任務」
- [x] `TimelineViewModes.vue` 甘特圖改為使用 `depends_on_task_ids`（取代目前自動串接）
- [x] 網狀圖視圖（ECharts）列為選配，不阻塞 7.2 MVP（本階段不實作）

**測試**：
- [x] `critical_path_service` 單元測試（DAG 建立、CPM 計算、impact 推估）
- [x] 邊界測試（循環依賴、缺失依賴、日期缺失）
- [x] 前端 risk-analysis 與 UI 互動測試

**驗收條件**：
- ✅ 系統能正確計算 critical path
- ✅ 風險項目清單可展示（包含 impact days 與建議動作）
- ✅ 循環依賴/缺失依賴不會造成 500，並可在 UI 看見 warnings
- ✅ 前端可視化清晰可理解
- ✅ 後端與前端測試各通過，無回歸

**時程建議**：
| 項目 | 人力日 | 備註 |
|------|---------|------|
| 後端 migration + CPM 邏輯 | 3 | networkx DAG 計算相對複雜 |
| 後端 blueprint | 1 | |
| 前端型別、service、UI | 2-3 | 視覺化與交互驗證需時 |
| 測試 | 2 | CPM 邊界情況較多 |
| **合計** | **~8-9** | 1.5-2 週 |

---

### 🟡 Phase 7.3：知識增強規劃（内部經驗版）（1-2 週）

**目的**：AI 協助使用者規劃新專案/任務，融合內部歷史與 AI 推理。

**詳細說明**：見 [Phase7_3_知識增強規劃詳解.md](Phase7_3_知識增強規劃詳解.md)。

**必要條件**：Phase 7.1/7.2 已驗收通過。

**需要的改動**：

**後端**：
- [ ] 新增 `services/rag_planning_service.py`（內部知識檢索 + AI 規劃鏈）
- [ ] 新增個人知識庫模組（可命名 `personal_knowledge_service.py`）
- [ ] 知識檢索採雙路：Timeline/Task SQL 檢索 + pgvector 語意檢索
- [ ] 新增 migration：`knowledge_documents`、`knowledge_chunks`、`pgvector` extension
- [ ] `blueprints/timelines.py` 新增 API：
  - `POST /api/timelines/ai-suggest-plan` （自然語言需求 → 規劃建議，含來源）
- [ ] 新增個人知識庫 API：
  - `POST /api/knowledge/documents`（上傳並索引）
  - `GET /api/knowledge/documents`（列表與狀態）
  - `DELETE /api/knowledge/documents/{id}`（刪除）

**前端**：
- [ ] `frontend/src/types/` 新增 `AIPlanSuggestion`、`SourceReference` 型別
- [ ] `frontend/src/services/timelineService.ts` 新增 `suggestPlan()`
- [ ] 任務建立流程加上「AI 規劃助手」對話框（輸入需求 → 看建議 → 使用/調整）
- [ ] Sidebar 新增「個人知識庫」組件（上傳、索引狀態、刪除/重建）

**測試**：
- [ ] `rag_planning_service` 單元測試（知識檢索準確度、規劃邏輯驗證）
- [ ] 個人知識庫測試（上傳解析、切塊索引、權限隔離）
- [ ] 前端 UI 互動測試

**驗收條件**：
- ✅ AI 規劃結果**必須有來源依據**（例如「參考歷史類似專案 #123」）
- ✅ 結果不可無來源就佛頭著糞
- ✅ 前端可看到建議骨架 + 來源標記
- ✅ 後端與前端測試各通過，無回歸

**時程建議**：
| 項目 | 人力日 | 備註 |
|------|---------|------|
| 後端知識檢索 + 規劃鏈 | 2-3 | 需確保來源追蹤 |
| 後端 blueprint | 1 | |
| 前端型別、service、UI | 2 | |
| 測試 | 1.5 | |
| **合計** | **~6.5-7.5** | 1-1.5 週 |

---

## 🚫 Phase 7 明確不做（避免功能膨脹）

- ❌ **PDF 匯出**：第一版先只做 JSON/簡單文本，UI 顯示即可
- ❌ **定時自動掃描**：先手動/API 觸發，定時掃描改 Phase 8
- ❌ **外部搜尋整合**：先只用內部歷史資料，外部搜尋改 Phase 8
- ❌ **MCP 工具擴充**：MCP 維持目前 4 個工具，Phase 8 才新增
- ❌ **複雜依賴表設計**：先用 JSON 欄位，後續再正規化
- ❌ **推薦系統**：先不做基於使用者行為的推薦序列

---

## 📊 各階段驗收與進階

### 7.1 → 7.2 進階條件
- Phase 7.1 測試全通過
- 使用者反饋週報與衝突提示「有用」（降低手工整理時間或早期發現衝突）
- 前後端無 regression

### 7.2 → 7.3 進階條件
- Phase 7.2 測試全通過
- 風險分析結果符合預期（CPM 準確 / 建議合理）
- 前後端無 regression

### 7.3 完成條件（Phase 7 上線）
- Phase 7.3 測試全通過
- AI 規劃結果來源依據明確
- 三個功能合起來能在產品中直接使用，不需特殊環境

---

## 🔧 實作細節速查

### 必新增的欄位
| 表 | 欄位 | 類型 | 用途 | 狀態 |
|-----|------|------|------|------|
| `task` | `completed_at` | timestamp(null) | 週報精確度 | 已完成（7.1） |
| `task` | `depends_on_task_ids` | JSON | 依賴關係 | 已完成（7.2） |
| `knowledge_documents` | `status`/`sha256`... | metadata | 個人知識庫文件管理 | 待實作（7.3） |
| `knowledge_chunks` | `embedding` | vector | 知識片段檢索 | 待實作（7.3） |

### 必新增的 Service
| Service | 用途 |
|---------|------|
| `weekly_report_service.py` | 週報聚合（可後續自 `timeline_service.py` 拆分） |
| `resource_conflict_service.py` | 衝突檢查（可後續自 `timeline_service.py` 拆分） |
| `critical_path_service.py` | CPM / 風險分析（7.2 必做） |
| `rag_planning_service.py` | 知識檢索 + AI 規劃（7.3） |
| `personal_knowledge_service.py` | 個人知識庫上傳、索引與查詢（7.3） |

### 必新增的 API
| 方法 | 路徑 | 階段 |
|------|------|------|
| GET | `/api/timelines/{id}/weekly-report` | 7.1 |
| POST | `/api/timelines/{id}/conflict-check` | 7.1 |
| GET | `/api/timelines/{id}/risk-analysis` | 7.2 |
| POST | `/api/timelines/ai-suggest-plan` | 7.3 |
| POST | `/api/knowledge/documents` | 7.3 |
| GET | `/api/knowledge/documents` | 7.3 |
| DELETE | `/api/knowledge/documents/{id}` | 7.3 |

### 必新增的套件
| 套件 | 版本 | 用途 | 階段 | 狀態 |
|------|------|------|------|------|
| networkx | 3.x | DAG/CPM 計算 | 7.2 | 已安裝 |
| tenacity | 8.x | AI 呼叫重試 | 7.3（可選先 7.1） | 已安裝 |
| pgvector (PostgreSQL extension) | 0.5+ | 向量檢索（與 PostgreSQL 同服務） | 7.3 | 待啟用 |

---

## 📝 建議實作順序

**週 1**： 7.1 基礎設施（migration + service + API）  
**週 2**： 7.1 前端 UI + 測試 + 驗收  
**週 3**： 7.2 CPM 邏輯  
**週 4**： 7.2 前端 UI + 測試 + 驗收  
**週 5**： 7.3 知識檢索 + 規劃鏈  
**週 6**： 7.3 前端 UI + 測試 + 驗收  

7.3 詳細執行請對照：[Phase7_3_知識增強規劃詳解.md](Phase7_3_知識增強規劃詳解.md)

---

## 🎯 KPI 與成功指標

| KPI | 目標 | 驗證方式 |
|-----|------|---------|
| 週報生成準確度 | 95% | 與手工週報比對 |
| 衝突預檢命中率 | 80% | 檢測「已建立後冒出的衝突」佔總比例 |
| 風險預警提前期 | 3+ 天 | 實際延期 vs 預警時間差 |
| AI 規劃建議採納率 | 40%+ | 使用者手動調整後採納比例 |

---

## 🚨 常見風險與緩解

| 風險 | 徵兆 | 緩解方案 |
|------|------|---------|
| CPM 計算不穩定 | 任務依賴缺失 / 循環依賴 | 先驗證資料清潔，後續補強邊界檢查 |
| AI 規劃無來源 | 結果籠統、無法追蹤 | code review 強制驗校，規劃結果含來源才上線 |
| 通知洪水 | 風險預警過度 | 先手動觸發，定時掃描再加 Phase 8 |
| 衝突提示誤報 | 使用者認為「假警報太多」| 調整閾值，可透過 A/B 測試驗證 |

---

## 📞 Phase 8 預留

Phase 7 完成後，Phase 8 可直接：
1. MCP 包裝現有 7.1/7.2/7.3 功能（無邏輯改動，純介面適配）
2. 新增定時掃描背景工作
3. 接入外部搜尋提供方

---

## ✅ 快速自檢清單

- [x] 我知道 Phase 7 的核心目標是「週報自動化 + 風險預警」
- [x] 我同意分階段（7.1 → 7.2 → 7.3）而不是一次全做
- [x] 我確認第一版不做「PDF 輸出」「定時掃描」「外部搜尋」「MCP 擴充」
- [x] 我已備妥 `networkx` 與 `tenacity` 套件清單
- [x] 我確認 7.3 採 `pgvector` + Sidebar 個人知識庫，不另開向量資料庫服務
- [x] 我理解各階段的驗收條件與進階條件
- [x] `task` 表已完成 `depends_on_task_ids` 與風險分析 API 串接

---

**下一步**：  
將此檔案轉入 Jira/GitHub Issues 拆任務，或直接指派開發順序。  
如有疑問，可參考 [Phase7_AI進階功能規劃.md](Phase7_AI進階功能規劃.md) 詳細版與 [Phase7_3_知識增強規劃詳解.md](Phase7_3_知識增強規劃詳解.md)。
