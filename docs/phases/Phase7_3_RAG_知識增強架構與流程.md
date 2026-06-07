# Phase 7.3 RAG 知識增強架構與流程

> 最後更新：2026/05/08
>
> 本文件用來說明 Phase 7.3 的後端知識增強能力：知識文件索引、向量檢索、RAG 規劃建議，以及這條鏈路中各個檔案的職責與資料流。
>
> 本次同步重點：補齊 Project Files authenticated preview/download、RAG text fallback、LLM timeout fallback，並確認 RAG source type 契約仍統一為 `timeline_task | knowledge_chunk`。

---

## 大綱

1. 這次做了什麼
2. 整體架構
3. 資料流流程
4. 各檔案作用
5. API 端點說明
6. 資料表與 migration
7. Embedding 與 provider 策略
8. 常見問題與設計取捨
9. 後續前端整合方向
10. 文件關聯與下一步

---

## 1) 這次做了什麼

Phase 7.3 的重點不是「再做一個 LLM 功能」，而是把知識增強流程整理成一條可以維運、可以追溯、可以擴充的後端主線。

這次完成的核心能力如下：

- 知識文件上傳與索引
  - 支援 `md`、`txt`、`pdf`
  - 解析文字、切塊、產生 embedding、寫入向量資料表
- 個人隔離的知識查詢
  - 以 `user_id` 作為所有查詢與寫入邊界
  - 避免不同使用者的知識互相混雜
- RAG 規劃建議
  - 同時整合「歷史任務」與「個人知識庫」來源
  - 將來源加權、去重、排序後，再交給 LLM 產生建議
- 可追溯輸出
  - 規劃結果一定帶 `source_references`
  - 若沒有任何來源，不會硬產生看起來像真的建議
- Embedding provider 化
  - 預設仍是 Gemini embedding
  - 但底層改成 LangChain provider 架構，方便未來切換 OpenAI / HuggingFace / Ollama

---

## 2) 整體架構

這條鏈路仍然遵守既有的分層原則：

```text
Blueprint -> Service -> Repository -> Model
```

### RAG 的實際分工

```text
[API Blueprint]
    ↓
[Knowledge Service / RAG Planning Service]
    ↓
[Repository 層：SQLAlchemy 查詢、向量檢索、資料更新]
    ↓
[Model 層：KnowledgeDocument / KnowledgeChunk]
```

### 文字流程版

```text
使用者上傳知識文件
  → blueprint 收 request
  → service 做驗證、解析、切塊
  → embedding service 產生向量
  → repository 寫入文件與 chunks
  → 後續規劃時再用歷史任務 + 知識庫做檢索
  → rag_planning_service 組合來源與上下文
  → chain 生成可追溯的建議結果
```

---

## 3) 資料流流程

這段是最重要的部分，分成「知識上傳索引」與「RAG 規劃建議」兩條路。

### 3.1 知識文件上傳與索引流程

```text
POST /api/knowledge/documents
  → 檢查登入身分（JWT）
  → 驗證檔案格式與大小
  → 讀取檔案內容並計算 sha256
  → 以 user_id + sha256 檢查是否重複
  → 文字解析（md/txt/pdf）
  → TextSplitterService 切塊
  → EmbeddingService 產生向量
  → KnowledgeRepository 寫入 document + chunks
  → document 狀態改為 ready
```

### 3.2 重建索引流程

```text
POST /api/knowledge/documents/:id/reindex
  → 若帶 project_id，先驗證是否為該 project 成員
  → 取得該 user 文件或該 project 文件
  → 讀取 document.source_text
  → 重新切塊與 embedding
  → 刪除舊 chunks
  → 寫入新 chunks
  → 更新 document 狀態
```

這裡的重要設計是：

- 不再用舊 chunks 拼回去重建
- 直接使用 `source_text`
- 這樣才不會因為 chunk overlap 或內容裁切導致重建越跑越歪

### 3.3 RAG 規劃建議流程

```text
POST /api/timelines/ai-suggest-plan
  → 驗證 payload
  → 抽出 user request
  → 查詢 timeline 歷史任務
  → 若啟用 personal knowledge，再查詢知識庫向量結果
  → 若啟用 project knowledge，且帶 project_id，則檢索專案共用知識
  → 兩類來源做加權、去重、排序
  → 組成 retrieval context
  → 呼叫 chain / LLM 產生規劃結果
  → 回傳 source_references 與 meta
```

---

## 4) 各檔案作用

下面用檔案為單位說明，這也是後續維護時最實用的部分。

### 4.1 `backend/models/knowledge.py`

這是知識文件與 chunk 的 ORM 定義。

#### `KnowledgeDocument`

作用：表示一份上傳的知識文件。

欄位重點：

- `user_id`：文件歸屬的使用者
- `project_id`：若為專案共用文件，綁定對應 timeline/project
- `filename`：原始檔名
- `mime_type`：來源 MIME type
- `size_bytes`：檔案大小
- `sha256`：用來做去重
- `source_text`：原始可索引全文，供 reindex 使用
- `status`：uploaded / indexing / ready / failed
- `error_message`：索引失敗時寫入原因
- `created_at` / `updated_at`：追蹤文件生命週期

#### `KnowledgeChunk`

作用：表示文件被切分後的一段文本與其向量。

欄位重點：

- `document_id`：所屬文件
- `user_id`：再次強制隔離
- `project_id`：專案共用文件檢索時的範圍鍵
- `chunk_index`：切塊順序
- `token_count`：切塊 token 估算值
- `content`：chunk 文字內容
- `embedding`：向量資料
- `chunk_metadata`：額外 metadata（例如 token count、來源資訊）

---

### 4.2 `backend/repositories/knowledge_repository.py`

這層只負責資料存取，不碰業務規則。

主要職責：

- 建立知識文件
- 依 `user_id` / `document_id` 查詢文件
- 依 `user_id + sha256` 查重
- 列出某個使用者的文件清單
- 列出某個文件的 chunks
- 用向量距離搜尋 chunks
- 取 chunk 數量
- 更新文件狀態
- 刪除並重建 chunks

#### 為什麼需要它

如果把 SQL 都放在 service 內，RAG 規則一多就會很難維護。現在把查詢抽到 repository 後：

- service 可以專心處理流程
- repository 可以專心處理 SQLAlchemy 查詢
- 後面要改索引策略時，影響面比較小

---

### 4.3 `backend/services/text_splitter_service.py`

這是文件切塊策略的核心。

主要職責：

- 先嘗試依 Markdown 標題切割
- 如果是一般文字，再依句號、換行、長度分段
- 保留 overlap，讓相鄰 chunk 之間有上下文
- 產生 `chunk_index` 與 `token_count`

#### 設計重點

這裡不是單純把文字切小段就好，而是要讓 chunk 盡量：

- 有語意完整度
- 不要太長，避免 embedding 過慢
- 不要太短，避免檢索時資訊太碎

所以它是「結構優先 + 長文 fallback」的策略。

---

### 4.4 `backend/services/embedding_service.py`

這是 embedding 產生器。

目前已改成 LangChain provider 架構：

- `google`：預設，使用 `langchain-google-genai`
- `openai`：可切換
- `huggingface`：本地模型
- `ollama`：本地 Ollama embedding

#### 主要作用

- `embed_documents(texts)`：用在知識索引
- `embed_query(text)`：用在規劃建議 / 搜尋時的 query embedding
- `embed_document(text)`：向後相容的單文件介面

#### 為什麼要改成 LangChain

原本如果直接綁死 Google SDK，未來切 provider 會很痛。改成 LangChain 後：

- 上層 service 不需要知道 provider 細節
- 想換模型只要改設定與對應套件
- 之後若要做更完整 RAG workflow，比較容易接到既有 LangChain chain

---

### 4.5 `backend/services/knowledge_service.py`

這是知識文件的主流程 service。

主要職責：

- 驗證檔案
- 讀取與解碼內容
- 產生 sha256
- 建立 document
- 切塊與 embedding
- 寫入 chunks
- 更新狀態
- reindex
- delete
- list

#### 重要流程節點

1. `_read_uploaded_file()`
   - 檢查檔案是否存在
   - 檢查副檔名
   - 檢查大小

2. `_decode_text_content()`
   - `md/txt`：做編碼容錯解碼
   - `pdf`：用 `pypdf` 抽文字

3. `upload_and_index_knowledge_document()`
   - 寫入 document
   - 切塊
   - 產 embedding
   - 寫 chunks
   - 完成後改為 `ready`

4. `reindex_knowledge_document()`
   - 不靠舊 chunk 回拼
   - 直接使用 `document.source_text`
   - 避免索引漂移

#### 為什麼它重要

這個 service 是整個知識索引的「主控制器」。
它把「檔案 -> 文字 -> chunk -> embedding -> DB」全部串起來。

---

### 4.6 `backend/services/rag_planning_service.py`

這是 Phase 7.3 的核心規劃服務。

主要職責：

- 驗證 payload
- 解析 user request
- 收集歷史任務來源
- 若需要，再收集個人知識來源
- 合併與加權來源
- 組出 retrieval context
- 呼叫 LLM 產生規劃建議
- 失敗時走 fallback

#### 來源組合邏輯

來源分成兩大類：

1. `timeline_task`
   - 使用者歷史任務
   - 包含任務名稱、備註、標籤等資訊

2. `knowledge_chunk`
   - 使用者自己上傳的知識文件 chunk
   - 透過 embedding 距離找出相關內容

#### 重要設計

- 不是把所有資料直接丟給 LLM
- 先做檢索與排序
- 再組 context
- 最後才生成結果

這樣可以減少 token 浪費，也比較容易控制品質。

#### fallback

如果 LLM 失敗，系統不會整個壞掉，而是回傳降級版本的建議。

---

### 4.7 `backend/chains/rag_planning_chain.py`

這是 AI chain 與輸出驗證層。

主要職責：

- 組裝 prompt chain
- 呼叫 `JsonOutputParser`
- 用 Pydantic schema 驗證輸出
- 驗證失敗時改用最小降級格式

#### 為什麼要有這一層

這層的價值是把「LLM 的不穩定輸出」關在這裡處理掉：

- service 不需要直接處理 prompt 細節
- schema 驗證失敗時可以降級
- 對外輸出維持固定 JSON contract

---

### 4.8 `backend/chains/schemas.py`

這裡定義了輸出契約。

Phase 7.3 主要會依賴這類結構：

- 規劃建議的 timeline 結構
- 建議任務列表
- 來源引用結構
- summary / meta 結構

它的作用是讓 LLM 回傳內容有明確格式，避免前端或後續流程接到奇怪資料。

---

### 4.9 `backend/prompts/rag_planning.py`

這裡集中管理規劃建議 prompt。

用途：

- 定義模型應該怎麼看待 user request
- 定義 retrieval context 的格式
- 要求輸出結構必須可解析
- 強制來源引用

這樣做的好處是：

- prompt 不會散落在 service 裡
- 未來要調整規劃品質，只要改 prompt 檔
- 文檔與實作可以對齊

---

### 4.10 `backend/blueprints/knowledge.py`

這是知識文件 API 的路由層。

主要端點：

- `POST /api/knowledge/documents`
- `GET /api/knowledge/documents`
- `DELETE /api/knowledge/documents/:id`
- `POST /api/knowledge/documents/:id/reindex`

備註：
- `POST/GET/DELETE/reindex` 皆可帶 `project_id` query（可選）。
- 當 `project_id` 存在時，會先驗證目前登入者是否為該專案成員。

這層不做複雜邏輯，只負責：

- JWT 身分驗證
- 收 request
- 呼叫 service
- 回 JSON response

---

### 4.11 `backend/blueprints/timelines.py`

這次主要新增：

- `POST /api/timelines/ai-suggest-plan`

它的角色是把 timeline 規劃的入口掛進既有專案路由，讓前端能直接對 timeline 做 AI 規劃請求。

---

### 4.12 `backend/app.py` 與 `backend/models/__init__.py`

這兩個檔案負責把新功能掛進應用啟動流程。

- `app.py`
  - 註冊 knowledge blueprint
  - 註冊 timelines 新 API
  - 載入 knowledge models，讓 migration / ORM 能正常運作

- `models/__init__.py`
  - 匯入 `KnowledgeDocument` / `KnowledgeChunk`
  - 確保其他模組可以直接引用這兩個模型

---

## 5) API 端點說明

### 5.1 知識文件 API

#### `POST /api/knowledge/documents`

用途：上傳文件並建立索引。

流程：

- 驗證格式與大小
- 解析文字
- 切塊
- embedding
- 寫入 document + chunks

可選參數：
- query `project_id`：上傳到指定專案共用檔案區（需該專案成員權限）。

#### `GET /api/knowledge/documents`

用途：列出某個使用者的知識文件。

可選參數：
- query `project_id`：列出該專案共用檔案（需該專案成員權限）。

#### `DELETE /api/knowledge/documents/:id`

用途：刪除知識文件與其 chunks。

可選參數：
- query `project_id`：刪除該專案共用文件（需該專案成員權限）。

#### `POST /api/knowledge/documents/:id/reindex`

用途：用 `source_text` 重新建立索引。

可選參數：
- query `project_id`：重建該專案共用文件索引（需該專案成員權限）。

---

### 5.2 規劃建議 API

#### `POST /api/timelines/ai-suggest-plan`

用途：根據使用者需求，結合歷史任務與個人知識來源，產生規劃建議。

主要請求欄位（新增）：
- `use_personal_knowledge`：是否納入個人知識庫（預設 true）
- `use_project_knowledge`：是否納入專案共用知識（預設 false）
- `project_id`：當 `use_project_knowledge=true` 時必填且需有專案成員權限

輸出重點：

- `suggested_timeline`
- `suggested_tasks`
- `source_references`
- `summary`
- `meta`

來源契約：

- `source_references[].source_type` 只使用 `timeline_task` 或 `knowledge_chunk`。
- 個人知識庫與專案共用檔案都以 `knowledge_chunk` 表示；是否來自專案範圍由檢索條件與未來 meta 擴充承載，不新增 `project_knowledge_document`。

#### 設計原則

- 沒來源，不輸出假建議
- 有來源，才允許回傳建議
- 建議內容必須可以追溯到來源

---

## 6) 資料表與 migration

### `knowledge_documents`

存放知識文件層級資料。

### `knowledge_chunks`

存放 chunk 與 embedding。

### migration 內容

本次 Phase 7.3 相關 migration 包含：

- 建立知識文件與 chunk 表
- 加 pgvector 支援
- 調整文件欄位
- 新增 `source_text`
- 調整唯一性與索引規則

---

## 7) Embedding 與 provider 策略

目前 `embedding_service.py` 已改成 LangChain provider 形式。

### 預設策略

- `EMBEDDING_PROVIDER=google`
- `EMBEDDING_MODEL=gemini-embedding-2`

### 可切換 provider

- `google`
- `openai`
- `huggingface`
- `ollama`

### 為什麼這樣設計

- 現階段仍以 Gemini 為主
- 但不想把整條知識管線綁死在單一 SDK
- 未來如果要做成本優化、本地化或 AB 測試，切換成本會低很多

---

## 8) 常見問題與設計取捨

### 8.1 為什麼 reindex 要存 `source_text`

因為 chunk 本身不是原始資料。
如果拿 chunk 再回拼，可能會發生：

- overlap 被重複帶入
- 切塊邊界漂移
- 重建結果越來越不像原文

所以要保留原始可索引全文。

### 8.2 為什麼不直接把所有內容丟給 LLM

因為這會：

- 成本高
- token 壓力大
- 品質不好控
- 無法明確說明來源

先做檢索與排序，再送入 LLM，才符合 RAG 的基本精神。

### 8.3 為什麼要分 repository / service / chain

這樣可以把責任拆開：

- repository：查資料
- service：管流程
- chain：管 prompt 與輸出格式

後續要換模型、換檢索策略、換 prompt，都比較不會牽一髮動全身。

---

## 9) 後續前端整合方向

目前後端已經完成，前端整合狀態如下：

- 規劃助手 UI（已初步接上）
  - 輸入需求
  - 顯示來源引用
  - 顯示推薦專案與任務草稿
- 個人知識文件管理 UI（已採獨立頁 `/knowledge`）
  - 上傳文件
  - 顯示文件列表與狀態
  - 刪除 / 重新索引
- Project Files（已在 `TimelineDetailDialog` 初步落地）
  - 專案檔案上傳、篩選、批次操作、下載、預覽、事件紀錄
- 來源可追溯視覺化（已初步接上，仍可後續拋光）
  - 讓使用者看得出這份建議是從哪些任務或哪些文件來的

---

## 10) 小結

Phase 7.3 的真正重點，是把「知識」從單次 AI 回答，變成可持續累積、可重建、可追溯的資料層。

目前這條線已經完成：

- 文件索引
- 向量檢索
- 規劃建議
- 來源引用
- provider 抽象

前端個人知識庫與 Project Files 已完成第一版可用閉環。接下來的主要工作，會從「能用」轉向「更準」：建立固定評測案例、調整來源排序、改善 prompt 與任務輸出品質。

---

## 10.1) 2026-05-08 實作補充

本輪穩定化完成：

- Project Files 下載/預覽改為 authenticated axios blob 請求，避免 SPA router 攔截 API URL。
- `rag_planning_service.py` 支援專案知識檢索，並在 vector 無結果或不可用時改走文字檢索 fallback。
- `ai-suggest-plan` 增加 LLM timeout fallback，避免模型逾時造成請求長時間卡住。
- `source_references[].source_type` 繼續維持 `timeline_task | knowledge_chunk`，個人知識與專案檔案都使用 `knowledge_chunk`。
- `KnowledgeDocumentEvent` 用於記錄 project files upload/indexed/index_failed/reindex/download/preview/delete。

---

## 11) 文件關聯與下一步

為了讓前端規劃討論更聚焦，建議搭配以下文件一起閱讀：

- `docs/Phase7_3_知識增強規劃詳解.md`：整體方案、API 契約與測試驗收視角
- `docs/Phase7_3_RAG_前端對齊與操作規劃.md`：前端實際操作點、使用路徑與對齊檢核清單

目前這份文件定位為「後端架構與資料流說明」，前端互動細節以對齊文件為主，避免把兩種目標混在同一份文件造成維護負擔。
