# Phase 7.3 知識增強規劃詳解（pgvector + 個人知識庫）

**文件狀態**: Draft v4（Phase 7.3 核心閉環完成，後續聚焦 RAG 品質調校）  
**最後更新**: 2026-05-08  
**適用階段**: Phase 7.3（承接 7.1 / 7.2 已完成能力）  
**核心選型**: PostgreSQL + pgvector（不新增獨立向量資料庫服務）
**本次同步**: 補齊 Project Files authenticated preview/download、RAG text fallback、LLM timeout fallback 與品質調校下一步

---

## 大綱（先看這裡）

1. 決策總結（本版定稿）
2. 目標與邊界
3. 架構設計（資料流與服務分層）
4. 選型說明（為何使用 pgvector）
5. 資料模型與 migration 規格
6. 檔案上傳與切塊流程（個人知識庫）
7. 檢索與排序策略（Timeline/Task + 個人知識庫）
8. API 契約（可直接實作）
9. 前端 Sidebar 組件規劃
10. 環境變數與運維策略
11. 測試策略與驗收標準
12. 與 Phase 7.2 銜接與預期 bug 清單
13. 里程碑與工時估算

---

## 1. 決策總結（本版定稿）

1. Phase 7.3 第一版資料來源固定為兩類：
   - 專案內歷史資料（Timeline/Task）
   - 使用者個人知識庫（Sidebar 入口，獨立頁 `/knowledge` 管理）
  - (新增) 專案共用檔案區（Project Files），可由專案成員上傳並在 RAG 規劃時選擇納入
2. 向量能力採 PostgreSQL `pgvector`，不另開 Milvus / Weaviate / Qdrant。
3. 外部搜尋（Google/Perplexity）維持 Phase 8 再開。
4. API 與回應需保證來源可追溯，禁止「無來源建議」。
5. 7.3 優先交付可用性與穩定性，不追求複雜 Agent runtime。
6. 後端主線（知識索引、RAG 規劃 API、來源可追溯）已完成，前端已新增個人知識庫獨立頁與 Project Files 初步操作區。
7. RAG `source_type` 契約統一為 `timeline_task | knowledge_chunk`；個人知識與專案檔案都不使用額外的 `project_knowledge_document` 類型。

---

## 2. 目標與邊界

### 2.1 目標

- 使用者輸入自然語言需求後，系統可產生「可落地」的專案/任務建議。
- 每條建議都能回溯來源（歷史任務或知識庫片段）。
- 建議內容與現有專案上下文一致，降低空泛回答比例。

### 2.2 邊界（本階段不做）

- 不做外部網路搜尋。
- 不做 PDF/Word 匯出。
- 不做跨使用者知識共享。
- 不做自動背景排程索引（先同步或手動重建）。

---

## 3. 架構設計（資料流與服務分層）

### 3.1 呼叫路徑

`Frontend -> Blueprint -> Service -> Repository -> PostgreSQL(pgvector) -> Chain/LLM`

### 3.2 核心流程

1. 使用者從 Sidebar 進入 `/knowledge` 並上傳檔案。
2. 後端解析檔案內容，切塊、embedding、寫入 `knowledge_chunks`。
3. 呼叫 `ai-suggest-plan` 時，系統先做雙路檢索：
   - 路徑 A: Timeline/Task 結構化歷史檢索
   - 路徑 B: 個人知識庫向量檢索
4. Service 層融合來源後交給規劃鏈，產生建議。
5. 回傳 `suggestions + source_references + confidence`。

### 3.3 分層責任

- Blueprint：驗證參數、權限、錯誤碼轉換。
- Service：檢索融合、提示詞組裝、降級策略。
- Repository：SQL / 向量查詢 / 分頁與過濾。
- Chain：純推理與結構化輸出（Pydantic）。

---

## 4. 選型說明（為何使用 pgvector）

### 4.1 採用 pgvector 的理由

- 與現有 PostgreSQL 共用同一套備份、權限、遷移流程。
- ACID 特性完整，資料一致性與交易語義較直觀。
- 可以在同一查詢中混合條件過濾 + 向量排序。
- 個人專案維運成本最低，不需再開新服務。

### 4.2 不採用獨立向量庫的理由（本階段）

- 新服務帶來額外部署、監控、備份與資料同步複雜度。
- 目前資料規模尚未到需要獨立向量集群。
- 先把產品價值跑通，再視資料量與延遲決定是否拆分。

---

## 5. 資料模型與 migration 規格

### 5.1 新增資料表

1. `knowledge_documents`
   - `id` (pk)
   - `user_id` (fk)
   - `filename`
   - `mime_type`
   - `size_bytes`
   - `sha256`
   - `status` (`uploaded|indexing|ready|failed`)
   - `error_message` (nullable)
   - `created_at`, `updated_at`
  - `project_id` (nullable int) — 若為專案共用檔案，會帶此欄位，表示該文件屬於某個 timeline/project

2. `knowledge_chunks`
   - `id` (pk)
   - `document_id` (fk)
   - `user_id` (fk)
   - `chunk_index`
   - `content`
   - `token_count`
   - `embedding` (vector)
   - `metadata` (jsonb)
   - `created_at`

### 5.2 索引與約束

- `knowledge_documents(user_id, created_at desc)`
- `knowledge_chunks(user_id, document_id, chunk_index)`
- `knowledge_chunks` 向量索引（資料量達門檻再啟用）
- `unique(user_id, sha256)` 避免重複上傳同檔案

### 5.3 Migration 內容

- 啟用 extension：`CREATE EXTENSION IF NOT EXISTS vector;`
- 建立上述兩張表與必要索引
- 回填策略：無（新功能新增，不影響舊資料）

---

## 6. 檔案上傳與切塊流程（個人知識庫）

### 6.1 支援格式（第一版）

- `md`, `txt`, `pdf`

### 6.2 上傳與索引步驟

1. 上傳檔案並建立 `knowledge_documents`（status=`uploaded`）。
2. 驗證大小/副檔名/使用者權限。
3. 解析文字內容（解析失敗標記 `failed`）。
4. 依固定策略切塊（建議 500-800 tokens，overlap 80-120）。
5. 產生 embeddings，批次寫入 `knowledge_chunks`。
6. 完成後更新 `status=ready`。

### 6.3 安全與限制

- 單檔大小上限建議 10MB。
- MIME type 與副檔名雙重驗證。
- 只允許讀取本人文件（所有查詢必帶 `user_id` 條件）。
- 專案共用檔案操作（list/delete/reindex）需帶 `project_id` 並通過專案成員驗證。

---

## 7. 檢索與排序策略（Timeline/Task + 個人知識庫）

### 7.1 檢索策略

- 路徑 A：結構化歷史檢索
  - 最近完成任務
  - 相似標籤與描述
  - 成功週報/風險處理案例
- 路徑 B：向量語意檢索
  - 從 `knowledge_chunks` 取 top-k 片段
  - 強制 user_id 篩選
  - 若為 project 檢索則以 `project_id` 範圍檢索（並先驗證成員權限）

### 7.2 融合策略（第一版）

- 固定比例融合，避免過早複雜化：
  - Timeline/Task 歷史: 60%
  - 個人知識庫: 40%
- 同來源去重（相同文件相近 chunk 只留較高分片段）。

### 7.3 回傳結構要求

- 每條建議都需附帶 `source_references[]`。
- 每個 reference 至少包含：
  - `source_type` (`timeline_task|knowledge_chunk`)
  - `source_id`
  - `title`
  - `snippet`
  - `score`

---

## 8. API 契約（可直接實作）

### 8.1 個人知識庫 API

1. `POST /api/knowledge/documents`
   - 上傳並索引文件
   - 可選 query：`project_id`（上傳至專案共用檔案區）
2. `GET /api/knowledge/documents`
   - 列出本人文件與索引狀態
   - 可選 query：`project_id`（列出該專案共用檔案）
3. `DELETE /api/knowledge/documents/{document_id}`
   - 刪除文件與 chunks
   - 可選 query：`project_id`（刪除該專案共用檔案）
4. `POST /api/knowledge/documents/{document_id}/reindex`
   - 重建索引（手動）
   - 可選 query：`project_id`（重建該專案共用檔案索引）

### 8.2 規劃 API（承接既有）

- `POST /api/timelines/ai-suggest-plan`
  - 請求新增欄位：
    - `use_personal_knowledge` (bool, default=true)
    - `use_project_knowledge` (bool, default=false)
    - `project_id` (int, required when `use_project_knowledge=true`)
    - `max_sources` (int, default=8)

### 8.3 回應契約（重點）

- `message`
- `suggested_timeline`
- `suggested_tasks[]`
- `source_references[]`
- `meta`（包含 token 用量、fallback 註記）

---

## 9. 前端個人知識庫頁規劃

### 9.1 組件目標

在 Sidebar 新增「知識庫」入口，導向獨立頁 `/knowledge`，提供：

- 上傳檔案
- 檔案列表與狀態
- 刪除/重建索引
- 在規劃助手切換是否使用知識庫
- 搜尋 / 狀態篩選 / 排序

### 9.2 狀態呈現

- `uploaded`：已接收，等待索引
- `indexing`：處理中
- `ready`：可用
- `failed`：失敗（顯示短錯誤）

### 9.3 交互重點

- 上傳後立即可見處理狀態，避免「無回應感」。
- 規劃結果視圖顯示來源標籤，提升可解釋性。

---

## 10. 環境變數與運維策略

### 10.1 Feature Flags

- `ENABLE_PHASE7_RAG_PLANNING=true`
- `ENABLE_PERSONAL_KNOWLEDGE_BASE=true`
- `ENABLE_PGVECTOR=true`

### 10.2 RAG 參數

- `EMBEDDING_PROVIDER=google`
- `EMBEDDING_MODEL=gemini-embedding-2`
- `RAG_MAX_CONTEXT_CHUNKS=8`
- `RAG_RETRIEVAL_TOP_K=12`

### 10.3 上傳限制

- `KNOWLEDGE_UPLOAD_MAX_MB=10`
- `KNOWLEDGE_ALLOWED_EXTENSIONS=md,txt,pdf`

---

## 11. 測試策略與驗收標準

### 11.1 後端測試

- Service 單元測試
  - 上傳/解析/切塊/索引
  - 雙路檢索與融合排序
  - 無來源時降級策略
- Blueprint 整合測試
  - 上傳 API 權限
  - 列表/刪除/重建索引
  - `ai-suggest-plan` 回應契約

### 11.2 前端測試

- Sidebar 元件互動測試
  - 上傳成功/失敗
  - 狀態更新
  - 刪除與重建索引
- 規劃助手測試
  - source references 顯示
  - 切換 `use_personal_knowledge`

### 11.3 驗收標準

- 規劃結果具可追溯來源。
- 查詢只會返回本人知識庫內容。
- 解析或 embedding 失敗時主流程不 500。
- 7.1/7.2 既有功能無回歸。

---

## 12. 與 Phase 7.2 銜接與預期 bug 清單

### 12.1 7.2 交接重點

- `depends_on_task_ids` 與風險分析邏輯維持不變。
- 7.3 僅擴充「規劃來源」，不改動 CPM 核心演算法。

### 12.2 預期 bug（優先排查）

1. embedding 維度不一致導致索引失敗。
2. 大檔案上傳造成請求 timeout。
3. 文件刪除後殘留 chunk（資料不一致）。
4. source reference 指向失效 id。
5. prompt context 過長導致模型回應截斷。

### 12.3 緩解策略

- 上線前固定 embedding model 與維度。
- 大檔解析採分段處理並加 timeout/fallback。
- 刪除文件使用 transaction 連動刪除 chunks。
- 回傳前做 source existence 驗證。

---

## 13. 里程碑與工時估算

| 工作項目 | 人力日 | 備註 |
|------|------|------|
| migration + repository | 1.5 | 建表與索引（已完成） |
| 上傳/解析/embedding pipeline | 2 | 含錯誤處理（已完成） |
| RAG 檢索融合與規劃鏈串接 | 2 | 含 source references（已完成） |
| 個人知識庫頁與整合 | 1.5 | 上傳 + 狀態 + 刪除 + 重建索引 + 篩選（已初步完成） |
| 測試與回歸 | 2 | 後端 + 前端（前端已補服務與頁面測試，仍需完整回歸） |
| **合計** | **~9** | 後端落地完成，前端主要入口已初步完成 |

---

## 14. 2026-05-07 補充（專案檔案區 P2）

### 14.1 Schema / Migration

- 新增 migration：`h_proj_kb_storage_evt`（銜接 `g_add_project_id_to_kb`）。
- `knowledge_documents` 補欄位：`file_path`、`storage_key`、`original_filename`、`deleted_at`。
- 新增 `knowledge_document_events` 事件表與 `project_id + created_at` 索引。

### 14.2 API / Service

- 新增：
  - `POST /api/knowledge/documents/batch-delete?project_id=`
  - `POST /api/knowledge/documents/batch-reindex?project_id=`
  - `GET /api/knowledge/documents/<id>/download?project_id=`
  - `GET /api/knowledge/documents/<id>/preview?project_id=`
  - `GET /api/knowledge/documents/events?project_id=`
- `GET /api/knowledge/documents` 新增 `q/sort/status` 篩選能力。
- project 檔案採「軟刪除 + 實體檔立即刪除 + 事件紀錄」策略。

---

## 15. 2026-05-07 補充（個人知識庫頁與 source type 契約）

- 新增 `/knowledge` 個人知識庫獨立頁，由 Sidebar「知識庫」入口進入。
- 個人知識庫頁使用不帶 `project_id` 的既有知識文件 API。
- 第一版支援上傳、列表、狀態、搜尋、篩選、排序、單檔刪除、單檔重建索引。
- Project Files 仍維持在 `TimelineDetailDialog` 內，並使用帶 `project_id` 的專案範圍 API。
- `source_references[].source_type` 統一為 `timeline_task | knowledge_chunk`；前端不再宣告或期待 `project_knowledge_document`。

---

## 16. 2026-05-08 補充（RAG 穩定化與可用閉環）

- 個人知識庫 `/knowledge` 與 Project Files 已完成第一版可用閉環。
- Project Files 下載/預覽改走 authenticated blob 請求，避免 SPA router 誤攔 `/api/knowledge/.../preview`。
- RAG 規劃已納入專案文件檢索；`project_id` 與 `use_project_knowledge` 控制是否使用專案範圍知識。
- Vector 檢索無命中或不可用時，後端會使用文字檢索 fallback，避免文件已 indexed 但規劃階段完全抓不到內容。
- LLM 呼叫加入 timeout fallback，模型逾時時仍可回傳 fallback 建議與來源。
- 下一輪重點改為品質工程：固定評測案例、來源排序調整、prompt 迭代、生成任務驗收標準。

---

## 補充

本文件是 Phase 7.3 的執行詳解，與以下文件互補：

- `docs/Phase7_AI進階功能規劃.md`（全域規劃版）
- `docs/Phase7_精簡執行版.md`（節奏與優先級版）
- `docs/Phase7_3_RAG_前端對齊與操作規劃.md`（前端操作與一致性確認版）
