# Learnlink Phase 7 重新規劃（執行版）
## 主線：LangChain + LangGraph；MCP 延後至 Phase 8

**文件狀態**: 決議版（Execution Ready）  
**最後更新**: 2026-04-22  
**適用範圍**: 以目前 Phase 6.6/6.6+ 程式碼為基線，推進 Phase 7 AI 進階能力  
**核心決策**: Phase 7 不依賴 MCP；先完成產品內 AI 能力。Phase 8 再把既有能力透過 MCP 對外開放。

---

## 大綱（先看這裡）

1. 決策總結與邊界
2. 目前專案基線（As-Is）
3. Phase 7 目標與範圍
4. Phase 7 架構原則（依現況落地）
5. 四大功能重排（不含詳細程式碼）
6. 分階段時程（7.1 / 7.2 / 7.3）
7. 需要新增或調整的項目（後端/前端/資料/測試/文件）
8. 依賴套件與環境變數
9. API 規劃（可直接實作）
10. 驗收標準與 KPI
11. 風險與緩解
12. Phase 8 MCP 介接策略（延後執行）
13. 立即執行清單（Next Actions）

---

## 1. 決策總結與邊界

### 1.1 最終決策

- Phase 7 主線：`LangChain + LangGraph` 完成產品內 AI 功能。
- Phase 8 主線：`MCP` 做外部工具/平台介接。
- 核心原則：業務邏輯只放在 `Service` 層，避免雙軌重複實作。

### 1.2 邊界定義

- Phase 7 內不新增 MCP 工具作為主要交付。
- Phase 7 產出的能力必須可由前端直接透過 REST API 使用。
- Phase 8 才做 MCP 包裝，且 MCP 只做「介面適配」，不重寫核心邏輯。

---

## 2. 目前專案基線（As-Is）

### 2.1 已具備能力（可直接承接）

- 後端已收斂為：Blueprint -> Service -> Repository -> Model。
- AI 鏈已上線：
  - `task_generation_chain.py`
  - `tool_selection_chain.py`
  - `summary_chain.py`
- Pydantic v2 驗證層已整合：`backend/chains/schemas.py`。
- LangGraph 範本已存在：`backend/chains/workflows.py`（目前未啟用，適合 Phase 7 激活）。
- 前端已有 `timelineService.ts` 與完整 Timelines/Tasks 視圖可接新 API。

### 2.2 現況限制（規劃需考慮）

- Task 模型已有 `estimated_hours` 與 `completed_at`；目前缺少 `depends_on_task_ids`（無法完整做 Critical Path 分析）。
- 7.1 的 `weekly-report` 與 `conflict-check` API 已落地，前端也已串接核心流程。
- 目前未見成熟背景排程框架（先以同步/手動觸發為主，再逐步升級）。
- MCP 已存在但定位應回到「外部接入層」，不作為 Phase 7 主流程。

---

## 3. Phase 7 目標與範圍

### 3.1 Phase 7 目標

- 從「AI 輔助記錄」升級到「AI 協助規劃與預警」。
- 完成四大能力：
  - 資源衝突偵測
  - 進度風險預警（Critical Path）
  - 週報自動生成
  - 知識增強規劃（內部經驗 + 個人知識庫；外部資訊延後）

### 3.2 Phase 7 不做

- 不做 MCP 工具大擴充。
- 不做多平台對外工具市場化。
- 不做過度複雜的 agent runtime 基建。

---

## 4. Phase 7 架構原則（依現況落地）

### 4.1 單一路徑原則

- 產品內呼叫路徑統一：
  - `Frontend -> Blueprint -> Service -> Chain/LangGraph -> LLM/DB`
- 不建立第二套平行邏輯。

### 4.2 Service 為核心

- 新功能先落在 `services/`。
- Blueprint 只做 I/O、權限、錯誤碼轉換。
- Chain/LangGraph 只做 AI 編排與推理，不承擔業務資料寫入規則。

### 4.3 漸進式複雜化

- 先完成可用 MVP（可同步呼叫）。
- 再導入 LangGraph 的多步狀態機與條件路由。
- 最後做性能與可觀測性優化。

---

## 5. 四大功能重排（不含詳細程式碼）

## 5.1 Feature A：資源衝突偵測與排程建議

**目標**: 新建或調整專案時，先檢查人力負載與日期衝突。  
**建議技術**: Service 主導 + LangChain 產生建議文字（不必先用 LangGraph）。

**需要的東西**:

- 資料面：沿用 `tasks.start_date/end_date/estimated_hours`，可選新增 `BusyPeriod`。
- 後端面：新增 `resource_conflict_service.py`。
- API 面：新增衝突檢查 endpoint。
- 前端面：Timeline 建立/編輯流程增加衝突提示 UI。

**交付結果**:

- 回傳是否衝突、衝突人員、建議日期區間。
- 使用者可選擇接受建議或維持原案。

---

## 5.2 Feature B：進度風險預警（Critical Path）

**目標**: 找出關鍵路徑任務，預測延期衝擊。  
**建議技術**: `networkx` 主計算 + `LangGraph` 漸進導入（先完成 Service 可用版）。

**需要的東西**:

- 資料面：Task 增加依賴資訊（先用 `depends_on_task_ids: int[]` JSON 欄位，後續再正規化）。
- 後端面：
  - `critical_path_service.py`（DAG/CPM 計算）
  - 在 `workflows.py` 增加可選的風險掃描工作流入口（不阻塞 MVP）
- API 面：新增 `risk-analysis` 查詢 endpoint（回傳 `critical_path` / `risk_items` / `warnings`）。
- 通知面：沿用既有通知機制，新增風險通知模板。
- 前端面：優先沿用既有甘特圖視圖，呈現「真依賴線 + 關鍵路徑高亮」；網狀圖列為選配。
- 邊界面：循環依賴、缺失依賴、日期不完整時不回 500，改回傳 warnings 提示。

**交付結果**:

- 顯示 critical path、每個風險項目的 impact days、建議處置。
- 能支援手動觸發分析；定時掃描列為 7.3 優化項。

---

## 5.3 Feature C：週報/總結自動生成

**目標**: 一鍵生成可閱讀的週報，並支援後續追蹤。  
**建議技術**: LangChain Summary Chain（先不必上 LangGraph）。

**需要的東西**:

- 資料面：Task 新增 `completed_at`（必要）。
- 後端面：新增 `weekly_report_service.py`。
- API 面：新增週報查詢與導出 endpoint。
- 前端面：Profile 或 Timeline 新增週報視圖。

**交付結果**:

- 提供完成率、風險摘要、下週重點。
- 首版可先即時計算；報告存檔可在 7.2/7.3 追加。

---

## 5.4 Feature D：知識增強規劃（RAG + 個人知識庫）

**目標**: 對使用者自然語言需求輸出更完整的專案與任務建議。  
**建議技術**: LangChain 工具調用 + LangGraph 編排（多來源融合）。

**需要的東西**:

- 內部知識 A：Timeline/Task 歷史資料檢索（SQL + 條件過濾）。
- 內部知識 B：Sidebar 個人知識庫（使用者上傳文件，切塊後向量化）。
- 向量層：採 PostgreSQL `pgvector`，不新增獨立向量資料庫服務。
- 後端面：新增 `rag_planning_service.py`（或 `knowledge_planning_service.py`）。
- API 面：新增個人知識庫上傳/查詢 API，並擴充 `ai-suggest-plan`。
- 詳細規格：見 [Phase7_3_知識增強規劃詳解.md](Phase7_3_知識增強規劃詳解.md)。

**交付結果**:

- 回傳：建議專案骨架、任務清單、來源摘要、建議理由。
- 明確標示「歷史資料」與「個人知識庫」的貢獻。

---

## 6. 分階段時程（7.1 / 7.2 / 7.3）

## 6.1 Phase 7.1（基礎能力落地，約 2-3 週）

**重點**: 先把資料與 API 地基打好。

- 確認 `completed_at` migration 已落地；依賴欄位留待 7.2 實作。
- 完成 Feature A MVP（衝突偵測）。
- 完成 Feature C MVP（週報即時生成）。
- 建立 API 契約與前端第一版視圖。

**出口條件**:

- 前端可用新 API 完成衝突檢查與週報查看。
- pytest + 前端測試通過，且既有流程不回歸。

## 6.2 Phase 7.2（風險引擎與 LangGraph 啟用，約 2-3 週）

**重點**: 先完成可上線的 CPM 風險引擎，再漸進啟用 LangGraph。

- 實作 Feature B（CPM + 風險提示 + 邊界 warnings）。
- 擴展 `workflows.py` 為可選風險分析工作流（Thin Workflow）。
- 串接通知通道，先提供手動觸發與 API 觸發。

**出口條件**:

- 可針對指定 timeline 回傳 critical path 與 risk flags。
- 循環依賴/缺失依賴可被辨識並回傳 warnings，不中斷主流程。
- 風險結果可在前端視圖展示並解讀。

## 6.3 Phase 7.3（知識增強與優化，約 2-4 週）

**重點**: 完成 Feature D 並優化穩定性。

- 落地 Timeline/Task + 個人知識庫的雙路檢索規劃。
- 完成 Sidebar 個人知識庫上傳、索引與狀態追蹤。
- 加入重試、快取與成本控制策略。
- 視需要導入定時掃描（若要背景任務）。

**出口條件**:

- 使用者輸入需求可得到含來源依據的規劃建議。
- 可觀測性（logs/metrics）到位，可追查 AI 輸出品質。

---

## 7. 需要新增或調整的項目（實作清單）

## 7.1 後端

- `models/task.py`
  - `completed_at` 已完成。
  - 7.2 新增依賴欄位（優先 `depends_on_task_ids`，後續再評估依賴關係表）。
- `services/`
  - `resource_conflict_service.py`（可後續自 `timeline_service.py` 拆分）
  - 新增 `critical_path_service.py`
  - `weekly_report_service.py`（可後續自 `timeline_service.py` 拆分）
  - 新增 `rag_planning_service.py`（命名可依團隊慣例）
- `chains/workflows.py`
  - 擴展為風險分析與知識規劃流程圖。
- `blueprints/timelines.py`（或新增 `reports.py`）
  - 新增 Phase 7 API 路由並接入 service。
- `migrations/versions/`
  - 新增 Phase 7 schema migration。
  - 7.3 新增個人知識庫表與 `pgvector` extension migration。

## 7.2 前端

- `frontend/src/services/timelineService.ts`
  - 增加衝突檢查、風險分析、週報、AI 規劃 API。
- `frontend/src/types/`
  - 補齊新回應型別（沿用集中型別策略）。
- `frontend/src/views/` 或 `frontend/src/components/`
  - 衝突提示 UI
  - 風險分析 UI
  - 週報 UI
  - 知識規劃結果 UI
  - Sidebar 個人知識庫 UI（上傳、索引狀態、刪除/重建索引）

## 7.3 測試與品質

- 後端：
  - service 單元測試（衝突檢查、CPM、週報聚合、知識融合）
  - blueprint 整合測試（新 API 契約）
  - 鏈輸出驗證測試（Pydantic + fallback）
- 前端：
  - 新 service 測試
  - 新視圖互動測試
- 回歸：
  - 既有 `generate-tasks`、`batch-create-tasks`、群組快照功能不得退化。

## 7.4 文件

- 更新 `docs/進度追蹤.md` 與 `docs/重構計畫.md` 的 Phase 7 狀態。
- 增補 `docs/phase7-runbook.md`（部署、回滾、排查流程）。
- 增補 `docs/Phase7_3_知識增強規劃詳解.md`（7.3 執行細節與選型）。

---

## 8. 依賴套件與環境變數

## 8.1 套件策略

- 已有可沿用：
  - `langchain`
  - `langgraph`
  - `pydantic>=2.0`
- 目前已在專案依賴，可直接沿用：
  - `networkx`（CPM / DAG）
  - `tenacity`（AI/外部請求重試）
- Feature D 可選：
  - PostgreSQL `pgvector` extension（7.3 建議直接採用）
  - `llama-index`（若要升級進階索引策略）

## 8.2 環境變數建議

- `ENABLE_PHASE7_CONFLICT_CHECK=true`
- `ENABLE_PHASE7_RISK_ANALYSIS=true`
- `ENABLE_PHASE7_WEEKLY_REPORT=true`
- `ENABLE_PHASE7_RAG_PLANNING=false`（分批開啟）
- `ENABLE_PERSONAL_KNOWLEDGE_BASE=false`（分批開啟）
- `RISK_ANALYSIS_MODE=manual`（後續可升級 scheduled）
- `EMBEDDING_PROVIDER=google-generativeai`
- `EMBEDDING_MODEL=text-embedding-004`
- `KNOWLEDGE_UPLOAD_MAX_MB=10`
- `KNOWLEDGE_ALLOWED_EXTENSIONS=md,txt,pdf`

---

## 9. API 規劃（可直接實作）

以下命名延續現有 `/api/timelines/*` 風格。

- `POST /api/timelines/{timeline_id}/conflict-check`
  - 用途：檢查資源衝突並回傳建議日期。
- `GET /api/timelines/{timeline_id}/risk-analysis`
  - 用途：回傳 critical path、風險衝擊與 warnings（循環/缺失依賴等）。
- `GET /api/timelines/{timeline_id}/weekly-report`
  - 用途：回傳指定週區間報告。
- `POST /api/timelines/ai-suggest-plan`
  - 用途：自然語言需求 -> 專案/任務建議（含來源依據）。
- `POST /api/knowledge/documents`
  - 用途：上傳個人知識庫文件並建立索引。
- `GET /api/knowledge/documents`
  - 用途：查詢個人知識庫文件與索引狀態。
- `DELETE /api/knowledge/documents/{document_id}`
  - 用途：刪除文件與向量 chunks。

API 回應原則：

- 保持與既有 payload 風格一致（snake_case 為主）。
- 每個 endpoint 至少回傳 `message` 或 `meta` 方便前端提示。
- `risk-analysis` 回傳需包含 `warnings` 欄位，避免邊界資料造成主流程中斷。
- 風險/建議內容需有可追溯來源欄位。

---

## 10. 驗收標準與 KPI

## 10.1 功能驗收

- Feature A：可檢測衝突並提供可用建議。
- Feature B：可算出 critical path 與延期影響。
- Feature C：可生成可讀週報，內容與資料一致。
- Feature D：可產生有來源依據的規劃建議。

## 10.2 品質驗收

- 後端測試與前端測試均通過。
- 鏈輸出異常時可降級，不中斷主流程。
- 主要 API 具備日志追蹤與錯誤可診斷性。

## 10.3 KPI 建議

- 衝突預警準確度 >= 80%
- 風險預警提前期 >= 2 天
- 週報人工修訂率 <= 30%
- 規劃建議採納率 >= 40%

---

## 11. 風險與緩解

- 風險：任務依賴資料不足導致 CPM 品質不穩。
  - 緩解：先允許部分依賴，缺資料時退回簡化風險規則。
- 風險：上傳解析或向量索引品質不穩。
  - 緩解：限制格式與大小、索引失敗可重試、回傳可讀錯誤訊息。
- 風險：LangGraph 流程過度複雜。
  - 緩解：先維持小圖（少節點），每次只擴一條路徑。
- 風險：無背景排程導致自動預警延後。
  - 緩解：先手動/API 觸發，後續再補排程。

---

## 12. Phase 8 MCP 介接策略（延後執行）

### 12.1 原則

- MCP 只包裝既有 API/Service。
- MCP 不承擔業務計算與 AI 核心邏輯。
- 單一真實邏輯來源仍為 backend services。

### 12.2 Phase 8 可開放的工具（示例）

- `timeline_conflict_check`
- `timeline_risk_analysis`
- `timeline_weekly_report`
- `timeline_ai_suggest_plan`

### 12.3 預期效益

- 對內維持簡潔架構。
- 對外可讓 Copilot/其他平台調用同一套能力。

---

## 13. 立即執行清單（Next Actions）

## 13.1 Sprint 0（本週可啟動）

- [ ] 確認 Phase 7 API 命名與 payload 契約。
- [ ] 建立 migration 規格（`depends_on_task_ids`）。
- [ ] 建立 `critical_path_service.py` 空殼（`weekly/conflict` 先沿用現有 `timeline_service.py`）。
- [ ] 在 `workflows.py` 增加 risk workflow 入口。
- [ ] 前端定義新 type 與 service method（先不做完整 UI）。

## 13.2 Sprint 1（Phase 7.1 收尾）

- [x] 完成 Feature A MVP。
- [x] 完成 Feature C MVP。
- [ ] 補齊前端 UI 互動測試（週報/衝突提示）。
- [ ] 更新進度文件。

## 13.3 Sprint 2（Phase 7.2）

- [ ] 完成 Feature B（含 LangGraph workflow）。
- [ ] 串接風險通知流程。

## 13.4 Sprint 3（Phase 7.3）

- [ ] 完成 Feature D（RAG：Timeline/Task + Sidebar 個人知識庫）。
- [ ] 完成 pgvector migration 與個人知識庫 API。
- [ ] 完成 [Phase7_3_知識增強規劃詳解.md](Phase7_3_知識增強規劃詳解.md) 的對照實作。
- [ ] 完成性能與可觀測性優化。

---

## 結語

本重排版已將策略固定為：

- Phase 7：先把產品內 AI 能力用 LangChain + LangGraph 做完整。
- Phase 8：再用 MCP 將既有能力對外暴露。

這樣可以同時兼顧：

- 開發效率（不重複寫邏輯）
- 架構一致性（Service 中心化）
- 後續擴展性（MCP 外部化）

---

*文件版本: 2.0（重排執行版）*