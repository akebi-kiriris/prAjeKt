# Phase 7.3 RAG 前端對齊與操作規劃

> 最後更新：2026/05/08
>
> 這份文件的目的不是講後端實作細節，而是確認「RAG 在產品上要達成什麼」、「使用者在前端要怎麼操作」，以及「我們現在的想法是否一致」。
>
> 本次同步重點：前端需對齊 `use_project_knowledge` / `project_id` 與 Project Files 操作路徑；個人知識庫採獨立頁面 `/knowledge`，由 Sidebar 提供入口。

---

## 大綱

1. 這份文件的用途
2. RAG 功能目標（產品視角）
3. 目標使用者與主要情境
4. 前端可操作區域總覽
5. 主要操作流程（使用者旅程）
6. 規劃結果頁要看見什麼
7. 一致性確認清單（你可直接改）
8. 非目標與邊界
9. 近期實作優先順序

---

## 1. 這份文件的用途

這份文件用來做三件事：

1. 把 RAG 功能目標講清楚，避免「有做功能但沒有對齊價值」。
2. 把前端操作點列清楚，避免開發時遺漏關鍵互動。
3. 提供一份可修改的對齊清單，讓你可以快速標記「同意 / 不同意 / 要調整」。

---

## 2. RAG 功能目標（產品視角）

Phase 7.3 的 RAG 在前端上，核心目標是下面四件事：

1. 更快開始規劃
- 使用者只要輸入需求，就能拿到可落地的專案與任務草稿。

2. 可追溯
- 每條建議都能看到來源，知道它來自歷史任務或知識文件，不是黑盒輸出。

3. 可調整
- 使用者可選擇是否納入個人知識庫，並可反覆重跑生成結果。

4. 可採納
- 結果不是一次性文字，而是能被使用者挑選後實際建立到專案中。

---

## 3. 目標使用者與主要情境

### 3.1 目標使用者

1. 專案發起者
- 手上有目標，但不知道怎麼拆解任務。

2. 團隊協作者
- 需要參考過去做法，避免重複踩坑。

3. 個人高頻使用者
- 會持續上傳文件，希望知識能累積並被用在後續規劃。

### 3.2 主要情境

1. 新專案啟動
- 輸入需求描述，快速拿到可執行草案。

2. 中途改版或加需求
- 針對既有專案補提案，並用來源來判斷可信度。

3. 依個人知識進行客製化建議
- 開啟 personal knowledge，讓規劃更貼合使用者習慣。

---

## 4. 前端可操作區域總覽

建議先以三個區塊落地：

1. 規劃助手區（Timeline 內）
- 輸入需求
- 觸發 AI 規劃
- 查看建議與來源
- 挑選任務後建立

2. 個人知識庫區（Sidebar 入口 + 獨立頁面）
- 上傳文件
- 查看索引狀態
- 刪除文件
- 手動 reindex

3. 建議結果檢視區（Dialog/Panel）
- 看 suggested timeline / tasks
- 看 source references
- 看摘要與 meta

---

## 5. 主要操作流程（使用者旅程）

### 流程 A：先上傳知識，再做規劃

1. 使用者從 Sidebar 進入 `/knowledge` 並上傳文件。
2. 文件進入 indexing，完成後變 ready。
3. 使用者到規劃助手輸入需求。
4. 開啟使用個人知識庫，送出生成。
5. 在結果區比對建議與來源。
6. 勾選任務並建立到專案。

### 流程 B：不使用個人知識，僅靠歷史任務

1. 使用者進入規劃助手。
2. 關閉 use personal knowledge。
3. 直接生成建議。
4. 看來源是否主要為 timeline task。
5. 採納部分任務並建立。

### 流程 C：結果不滿意，做二次調整

1. 修改需求描述（加限制、時程、角色）。
2. 重新生成。
3. 比對新舊來源與任務草稿。
4. 最終採納可用任務。

---

## 6. 規劃結果頁要看見什麼

這是前端落地時最容易漏掉的區塊，建議明確固定：

1. 建議內容
- suggested timeline（名稱、摘要）
- suggested tasks（名稱、優先級、估時、依賴）

2. 來源資訊
- source type（timeline task / knowledge chunk）
- title
- snippet
- score

3. 可信度與可操作資訊
- 是否啟用 personal knowledge
- 來源總數
- 是否 fallback

4. 操作按鈕
- 全選/取消任務
- 建立選取任務
- 重新生成
- 返回編輯需求

---

## 7. 一致性確認清單（你可直接改）

請用下面三種標記快速確認：
- 同意：保留
- 不同意：改寫條目
- 待討論：先註記問題

### 7.1 目標一致性

1. 我們的目標是「可採納的規劃草稿」，不是單純聊天回答。
2. 我們要強制顯示來源，避免黑盒建議。
3. 沒有來源時，不應顯示看起來完整但不可追溯的建議。

### 7.2 介面一致性

1. 規劃助手內一定要有「是否使用個人知識庫」的顯示與切換。
2. Sidebar 要看得到文件狀態（uploaded/indexing/ready/failed）。
3. 建議結果一定要有可採納操作（至少支援挑選任務建立）。

### 7.3 體驗一致性

1. 使用者在 1-2 次操作內就能完成「輸入需求 -> 生成 -> 建立」。
2. 失敗情境要有可理解訊息（例如索引失敗、無可用來源）。
3. 結果不佳時，重新生成路徑要清楚，不要讓人卡住。

---

## 8. 非目標與邊界

本輪先不做：

1. 外部網路搜尋整合。
2. 跨使用者知識共享。
3. 複雜 Agent 多步編排 UI。
4. 高度自動化的背景索引工作流可視化。

---

## 9. 近期實作優先順序

### P0（先做）

1. 規劃助手
- 需求輸入
- 生成按鈕
- 結果與來源顯示
- 任務採納建立
- `use_personal_knowledge` / `use_project_knowledge` 切換
- `use_project_knowledge=true` 時帶入 `project_id`

2. 個人知識庫頁基礎（Sidebar 入口 `/knowledge`）
- 上傳
- 列表
- 狀態顯示
- 刪除
- 重建索引
- 搜尋 / 狀態篩選 / 排序

3. 專案檔案區（Project Files / Sidebar）
- 顯示該專案成員上傳的共用文件
- 支援上傳、刪除、重建索引（僅限專案成員）
- 所有 project files 操作帶 `project_id` query
- 在規劃助手可切換是否納入專案檔案

### P1（接著做）

1. Reindex 操作與錯誤提示優化。
2. 結果區的來源篩選（只看任務來源/只看知識來源）。
3. 重新生成前後結果差異提示。

### P2（後續）

1. 使用者偏好（預設是否開啟 personal knowledge）。
2. 來源品質分析（哪些來源常被採納）。

---

## 10. 2026-05-07 實作更新（P2 專案檔案區）

已落地：

1. 後端 API 擴充：`batch-delete`、`batch-reindex`、`download`、`preview`、`events`。
2. `GET /api/knowledge/documents` 支援 `q/sort/status` 參數。
3. 專案檔案原始檔保存路徑：`UPLOAD_FOLDER/project_knowledge/<project_id>/...`。
4. `TimelineDetailDialog` 新增專案檔案區 UI：上傳、搜尋/排序/狀態、批次選取操作、下載/預覽、最近操作歷史。
5. RAG 端維持 `use_project_knowledge + project_id` 請求對齊。

待補強：

1. 前端視覺細節與互動拋光（分頁、狀態圖示一致化）。
2. 前後端測試在目前本機環境需先補齊 `pytest` 與處理 `vitest spawn EPERM` 後再完整回歸。

---

## 11. 2026-05-07 實作更新（個人知識庫獨立頁與契約對齊）

已落地：

1. Sidebar 新增「知識庫」入口，導向 `/knowledge`。
2. 新增個人知識庫獨立頁，支援上傳、列表、搜尋、狀態篩選、排序、刪除、單檔重建索引。
3. 個人知識庫頁操作不帶 `project_id`，與 Project Files 的專案範圍操作分開。
4. RAG 來源契約統一為 `timeline_task | knowledge_chunk`。
5. 前端來源顯示改為產品語言：`timeline_task` 顯示「歷史任務」，`knowledge_chunk` 顯示「知識文件」。

契約說明：

- 個人知識與專案檔案在 RAG source type 上都使用 `knowledge_chunk`。
- 若未來需要區分個人/專案來源，不再新增 `project_knowledge_document` source type，而是另行設計 meta 欄位。

---

## 12. 2026-05-08 實作更新（Project Files 與 RAG 穩定化）

已落地：

1. Project Files 的下載與預覽改走 `timelineService` axios blob 請求，帶 JWT header，避免瀏覽器把 `/api/knowledge/documents/{id}/preview` 當成 Vue Router 路由。
2. 專案檔案區新增最近操作紀錄，操作類型包含 upload、indexed、index_failed、reindex、download、preview、delete。
3. RAG 規劃已能同時納入個人知識與專案文件；專案文件由 `project_id` + `use_project_knowledge` 控制。
4. 當 vector 檢索沒有命中或向量能力不可用時，後端會使用文字檢索 fallback，降低「文件已上傳但 RAG 讀不到」的機率。
5. `ai-suggest-plan` 加入 LLM timeout fallback；模型逾時時仍回傳可用的 fallback 建議與來源，而不是讓前端長時間等待。

後續補強：

1. RAG 生成品質與 prompt 需要用固定案例評測。
2. Project Files / RAG Planning 已讓 `TimelineDetailDialog.vue` 明顯變重，後續建議拆成獨立 panel components。

---

## 備註

如果你想用最短時間確認方向，建議你只先看三段：

1. 第 2 節：RAG 功能目標
2. 第 4 節：前端可操作區域
3. 第 7 節：一致性確認清單

你只要把第 7 節標成「同意/不同意/待討論」，我們就能很快把前端規劃收斂成可實作版本。
