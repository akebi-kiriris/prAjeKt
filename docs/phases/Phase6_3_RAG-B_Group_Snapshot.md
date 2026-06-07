# Phase 6.3 — RAG‑B：Group 知識快照（Group Snapshot）

目標
- 自動產出群組在指定時間窗（預設 30 天）的知識快照，內容包含：topics、decisions、action_items、notable_quotes，且每一項需附上來源 message id 以供追溯。

驗收條件（簡要）
- 小型群組（<= 500 條訊息）：同步產生並在 30s 內回傳結果。
- 大型群組（> threshold）：回傳 202 並以 background job 完成，最終結果儲存於 DB 並可查詢。
- Snapshot 必須包含指定欄位並保留來源 id；MockProvider 測試通過。

高階任務（短清單）
- 設計 DB schema + migration
- 新增 `GroupAISnapshot` model
- 後端 service：抓訊息 → chunk → 呼叫 AI → 合併 → persist
- API：同步/非同步觸發 endpoint（含 permission）
- 背景 job + job status API
- 前端：service + UI（觸發、預覽、下載、Job 狀態）
- 撰寫單元 + 整合測試（MockProvider）
- 監控指標與限流/重試策略

環境變數（建議）
- `AI_PROVIDER`=gemini|mock（已存在）
- `AI_MODEL`=gemini-2.5-flash-lite（已存在）
- `SNAPSHOT_WINDOW_DAYS`=30
- `SNAPSHOT_ASYNC_THRESHOLD`=500
- `SNAPSHOT_CHUNK_SIZE`=50

要改 / 要新增的檔案與關鍵函數（清單）

- Models / Migrations
  - 新增：`backend/models/group_ai_snapshot.py`
    - 類別：`GroupAISnapshot`（欄位：id, group_id, summary_json, created_by, created_at, source_count, model, provider, metadata）
  - 新增 Alembic migration：`backend/migrations/versions/<rev>_create_group_ai_snapshots.py`

- 後端 Service（修改）
  - 修改：`backend/services/group_service.py`
  - 新增／實作的函數：
    - `generate_group_snapshot(group_id, window_days=30, created_by=None, force=False)` — 主流程
    - `fetch_group_messages(group_id, window_days)` — 撈取來源訊息（過濾、排序）
    - `chunk_messages(messages, size)` — 切片
    - `build_chunk_prompt(chunk)` — 建 prompt（帶 message ids）
    - `parse_ai_response(raw)` — 解析 provider 回傳 JSON
    - `merge_chunk_summaries(chunk_summaries)` — 合併多 chunk 結果
    - `persist_snapshot(snapshot_dict, metadata)` — 寫入 `GroupAISnapshot`
    - `enqueue_snapshot_job(group_id, window_days, user_id)` — 排 queue（若採用非同步）

  - 注意：呼叫 `get_ai_provider()`（`backend/services/ai_provider.py`）以切換 provider/model

- Blueprint / API（修改）
  - 修改：`backend/blueprints/groups.py`
    - 新增 route：`POST /api/groups/<group_id>/ai-snapshot`（驗證成員、接受 `{window_days, async}`）
  - 新增（如需 job 查詢）：`backend/blueprints/jobs.py`
    - `GET /api/jobs/<job_id>` 回傳 job 狀態與結果 id

- Background Worker（新增）
  - 新增：`backend/workers/snapshot_worker.py`
    - 函數：`process_group_snapshot_job(job_id, group_id, window_days, requested_by)`
  - 選擇：Redis+RQ 或 Celery（config + Docker/Procfile 說明）

- 前端（修改/新增）
  - 修改：`frontend/src/services/groupService.ts`（或相對應 js）
    - `generateSnapshot(groupId, windowDays=30, async=false)`
    - `getJobStatus(jobId)`
  - 新增元件：`frontend/src/components/GroupSnapshotCard.vue`（預覽、下載、重新生成、釘選）
  - 修改 view：`frontend/src/views/GroupsView.vue` 加入口與狀態顯示

- 測試（新增）
  - 新增：`backend/tests/services/test_group_snapshot.py`（單元：chunk、merge、prompt builder；MockProvider）
  - 新增：`backend/tests/blueprints/test_groups_snapshot.py`（整合：endpoint、permission、async 行為）
  - 前端：vitest 測試 `groupService.generateSnapshot()` 與 `GroupSnapshotCard.vue`

測試策略（重點）
- 單元：測 `chunk_messages`、`merge_chunk_summaries`、`build_chunk_prompt`（使用 `MockProvider`）
- 整合：endpoint 測試透過 monkeypatch `get_ai_provider()` 回傳 `MockProvider`，驗證同步結果與 202+queue 行為
- 壓力：超過 `SNAPSHOT_ASYNC_THRESHOLD` 時應回 202

監控與指標（建議）
- `snapshot_generation_time_seconds`（histogram）
- `snapshot_source_count`（gauge）
- `snapshot_success_total` / `snapshot_failure_total`
- `snapshot_jobs_queue_length`

估時（粗略）
- Schema + migration：0.5 天
- 後端 service：2 天
- Endpoint + job queue：1 天
- Background worker：1 天
- 前端 UI + service：1 天
- 測試與修正：1–2 天
- Beta 評估與 prompt 調整：1 週

下一步（建議）
1. 先建立 migration + model（小步驟，驗證 schema）
2. 在 `group_service` 實作 `generate_group_snapshot` 的基礎流程（以 `MockProvider` 驗證）
3. 新增 endpoint 並跑整合測試

待辦（短 checklist）
- [x] 新增 migration + `GroupAISnapshot` model
- [x] 完成 `group_service.generate_group_snapshot`
- [x] 新增 `POST /api/groups/<id>/ai-snapshot` endpoint
- [x] 實作 background worker + job API
- [x] 前端 snapshot UI 與 service（`groupService` + `GroupsView` 快照操作與預覽）
- [x] 單元/整合測試（後端）
- [ ] Beta 評估

檔案：`docs/Phase6_3_RAG-B_Group_Snapshot.md`

---

## 群組對話範例（可逐步手動發送）

用途：以下訊息可分批貼進群組，幫你快速累積可用資料讓 6.3 snapshot 有內容可摘要。

建議發送節奏
- 每天貼 6-10 則
- 連續 10-14 天
- 混合「決議 / 風險 / 行動項 / 一般討論」

### 批次 A：需求與排程（第 1-3 天）

Day 1
1. 我們這週目標是把 Group Snapshot API 做到可以回傳 topics/decisions/action_items。
2. 我建議先做同步版本，訊息量大再切 async。
3. 目前風險是 message schema 不一致，可能要先做 normalize。
4. 今天先產出 migration 與 model，明天接 service。
5. 決議：`SNAPSHOT_WINDOW_DAYS` 預設 30。
6. 行動：我今晚補上 endpoint 規格文件。

Day 2
1. model 我加了 `summary_json` 與 `metadata_json`，方便後續追蹤。
2. 我們需要每個 action item 帶 `message_ids`，不然不可追溯。
3. 風險：AI 可能回傳非 JSON，要加 parse fallback。
4. 決議：parse 失敗直接回 500 並記錄錯誤訊息。
5. 行動：明天補 `merge_chunk_summaries` 單元測試。
6. 我會再補一批模擬聊天資料，讓 snapshot 不會太空。

Day 3
1. 今天先確認權限：只有 group member 才能產生 snapshot。
2. 如果 `source_count` 超過 threshold，改走 background job。
3. 風險：非同步 job 在本地重啟會遺失 in-memory 狀態。
4. 決議：先用輕量 in-memory，Phase 6.3.x 再接 Redis。
5. 行動：增加 `GET /api/groups/snapshot-jobs/{job_id}`。
6. 明天要補最新快照查詢 API。

### 批次 B：實作細節與測試（第 4-7 天）

Day 4
1. 我剛測了 chunk size=50，對短訊息群組是夠用的。
2. 建議在 prompt 裡保留 sender 與 created_at，摘要品質比較穩。
3. 風險：同義 topic 會重複，需要 merge 去重。
4. 決議：topic 去重 key 用 title.lower()。
5. 行動：今天補 `merge_chunk_summaries` 去重規則。
6. 明天我會跑整包 pytest 確認沒有回歸。

Day 5
1. 今天測試結果：非 member 打 snapshot API 會被擋 403。
2. 我補了成功路徑測試，能拿到 summary 與 snapshot_id。
3. 風險：若 provider timeout，可能需要重試策略。
4. 決議：先回 503，重試留到後續優化。
5. 行動：補 job status completed/failed 狀態欄位。
6. 另外我會寫一些「可引用」的對話句子給 notable_quotes。

Day 6
1. 我覺得 action_items 要求 `assignee` 可空，避免模型亂填。
2. 這批資料裡我會刻意放幾句有 deadline 的訊息。
3. 風險：日期格式不一，建議先接受字串，不做嚴格 parse。
4. 決議：`due` 先維持 nullable string。
5. 行動：補 latest snapshot API 測試。
6. 明天整理一次 docs 與範例資料。

Day 7
1. 我們這週里程碑：model/migration/service/api/tests 都已打通。
2. 下週先做前端 snapshot 卡片與 job 狀態輪詢。
3. 風險：群組資料太少時，summary 會偏空。
4. 決議：上線前先手動灌 100 則測試對話。
5. 行動：我今天先發 20 則，剩下分 3 天補齊。
6. 記得每則訊息都盡量有上下文，AI 比較容易抽出 topics。

### 批次 C：真實協作語氣（第 8-10 天）

Day 8
1. 大家早，我先把昨天的 endpoint 錯誤碼整理到文件。
2. 如果今天有空，請幫我看一下 action_items 的可讀性。
3. 我發現有些決議句子太短，可能要補前後文。
4. 先決議：本週不引入新依賴，避免部署風險。
5. 我晚點會補兩個 edge case：空訊息與 deleted 訊息。
6. 若沒問題，明天開始做前端卡片版型。

Day 9
1. 今天測了 120 則訊息，snapshot 還在可接受延遲。
2. 如果超過 500 則，背景 job 流程有成功觸發。
3. 風險：job 狀態目前放記憶體，服務重啟就不見。
4. 決議：beta 先接受，正式版改 Redis。
5. 行動：我來補一版部署備註與回滾步驟。
6. 大家如果看到摘要有誤，直接貼原始 message id 給我。

Day 10
1. 這輪成果可以 demo 了：從群組聊天到自動快照。
2. 建議下一輪做「每週自動 snapshot」排程任務。
3. 我想把 notable_quotes 也顯示在前端卡片上。
4. 決議：Phase 6.3 收斂後再開 6.4。
5. 行動：今天先收集 20 筆人工評分。
6. 收尾：我會把這批對話再複製到第二個群組做 A/B 比較。

### 快速貼文模板（懶人版）

你也可以直接用這 12 句輪流貼：
1. 今天決議先做 API，不先做前端。
2. 目前風險是 AI 回傳可能不是 JSON。
3. 行動項：明天下午補完 service 單元測試。
4. 指派：這題由我負責，期限週五。
5. 如果訊息量超過門檻，就改背景 job。
6. 我們需要每個重點都附 message ids。
7. 先把 migration 跑完，再驗證 endpoint。
8. 剛剛測試過，非成員呼叫 API 會回 403。
9. 下一步是做 job status 查詢。
10. 若摘要品質下降，先調整 prompt 與 chunk size。
11. 本週目標是能穩定產出 topics/decisions/action_items。
12. 下週再進入前端卡片與 Beta 評估。


### 結果

Group Snapshot API 功能
來源 message_ids: 15
API 同步與非同步版本考量
來源 message_ids: 16
Message Schema 不一致風險與處理
來源 message_ids: 17
Migration 與 Model 產出
來源 message_ids: 18
Model 欄位新增 (`summary_json`, `metadata_json`)
來源 message_ids: 21
Action Item 追溯性要求 (`message_ids`)
來源 message_ids: 22
AI 回傳非 JSON 風險與處理
來源 message_ids: 23
權限控管：僅限群組成員產生 snapshot
來源 message_ids: 27
Background Job 觸發條件 (`source_count` threshold)
來源 message_ids: 28
非同步 Job 本地重啟狀態遺失風險
來源 message_ids: 29
Chunk Size 測試結果
來源 message_ids: 33
Prompt 設計建議 (保留 sender 與 created_at)
來源 message_ids: 34
同義 Topic 重複與合併去重
來源 message_ids: 35
Provider Timeout 處理與重試策略
來源 message_ids: 41
Action Item Assignee 可空設計
來源 message_ids: 45
日期格式不一風險與處理
來源 message_ids: 47
群組資料太少導致 Summary 偏空風險
來源 message_ids: 53
訊息上下文對 Topic 抽取的影響
來源 message_ids: 56
Endpoint 錯誤碼整理
來源 message_ids: 57
Action Item 可讀性檢視
來源 message_ids: 58
決議句子長度與上下文
來源 message_ids: 59
本週不引入新依賴
來源 message_ids: 60
Edge Case 處理 (空訊息, deleted 訊息)
來源 message_ids: 61
訊息數量與快照延遲
來源 message_ids: 63
背景 Job 觸發測試 (超過 500 則)
來源 message_ids: 64
Job 狀態儲存
來源 message_ids: 65
下一輪開發主題
來源 message_ids: 70
前端功能需求
來源 message_ids: 71
專案階段規劃
來源 message_ids: 72
本輪成果
來源 message_ids: 69
✅ Decisions
`SNAPSHOT_WINDOW_DAYS` 預設 30。
來源 message_ids: 19
Parse 失敗直接回 500 並記錄錯誤訊息。
來源 message_ids: 24
先用輕量 in-memory，Phase 6.3.x 再接 Redis。
來源 message_ids: 30
Topic 去重 key 用 title.lower()。
來源 message_ids: 36
先回 503，重試留到後續優化。
來源 message_ids: 42
`due` 先維持 nullable string。
來源 message_ids: 48
上線前先手動灌 100 則測試對話。
來源 message_ids: 54
本週不引入新依賴，避免部署風險。
來源 message_ids: 60
Beta 版本先接受 job 狀態放記憶體，正式版改用 Redis。
來源 message_ids: 66
Phase 6.3 收斂後再開 6.4。
來源 message_ids: 72
🧭 Action Items
今晚補上 endpoint 規格文件。
assignee: 吳育嘉 | due: 未指定
來源 message_ids: 20
明天補 `merge_chunk_summaries` 單元測試。
assignee: 未指定 | due: 明天
來源 message_ids: 25
補一批模擬聊天資料，讓 snapshot 不會太空。
assignee: 吳育嘉 | due: 未指定
來源 message_ids: 26
增加 `GET /api/groups/snapshot-jobs/{job_id}`。
assignee: 未指定 | due: 未指定
來源 message_ids: 31
補最新快照查詢 API。
assignee: 吳育嘉 | due: 明天
來源 message_ids: 32
今天補 `merge_chunk_summaries` 去重規則。
assignee: 未指定 | due: 今天
來源 message_ids: 37
明天跑整包 pytest 確認沒有回歸。
assignee: 吳育嘉 | due: 明天
來源 message_ids: 38
補 job status completed/failed 狀態欄位。
assignee: 未指定 | due: 未指定
來源 message_ids: 43
寫一些「可引用」的對話句子給 notable_quotes。
assignee: 吳育嘉 | due: 未指定
來源 message_ids: 44
補 latest snapshot API 測試。
assignee: 未指定 | due: 未指定
來源 message_ids: 49
整理一次 docs 與範例資料。
assignee: 吳育嘉 | due: 明天
來源 message_ids: 50
今天先發 20 則對話，剩下分 3 天補齊。
assignee: 吳育嘉 | due: 今天
來源 message_ids: 55
補兩個 edge case：空訊息與 deleted 訊息。
assignee: 吳育嘉 | due: 晚點
來源 message_ids: 61
明天開始做前端卡片版型。
assignee: 未指定 | due: 明天
來源 message_ids: 62
補一版部署備註與回滾步驟。
assignee: 吳育嘉 | due: 未指定
來源 message_ids: 67
收集 20 筆人工評分。
assignee: 吳育嘉 | due: 今天
來源 message_ids: 73
將這批對話複製到第二個群組做 A/B 比較。
assignee: 吳育嘉 | due: 未指定
來源 message_ids: 74
💬 Notable Quotes
「我們這週目標是把 Group Snapshot API 做到可以回傳 topics/decisions/action_items。」
來源 message_id: 15
「我建議先做同步版本，訊息量大再切 async。」
來源 message_id: 16
「目前風險是 message schema 不一致，可能要先做 normalize。」
來源 message_id: 17
「今天先產出 migration 與 model，明天接 service。」
來源 message_id: 18
「我們需要每個 action item 帶 `message_ids`，不然不可追溯。」
來源 message_id: 22
「風險：AI 可能回傳非 JSON，要加 parse fallback。」
來源 message_id: 23
「今天先確認權限：只有 group member 才能產生 snapshot。」
來源 message_id: 27
「如果 `source_count` 超過 threshold，改走 background job。」
來源 message_id: 28
「風險：非同步 job 在本地重啟會遺失 in-memory 狀態。」
來源 message_id: 29
「我剛測了 chunk size=50，對短訊息群組是夠用的。」
來源 message_id: 33
「建議在 prompt 裡保留 sender 與 created_at，摘要品質比較穩。」
來源 message_id: 34
「風險：同義 topic 會重複，需要 merge 去重。」
來源 message_id: 35
「明天我會跑整包 pytest 確認沒有回歸。」
來源 message_id: 38
「今天測試結果：非 member 打 snapshot API 會被擋 403。」
來源 message_id: 39
「我補了成功路徑測試，能拿到 summary 與 snapshot_id。」
來源 message_id: 40
「風險：若 provider timeout，可能需要重試策略。」
來源 message_id: 41
「我覺得 action_items 要求 `assignee` 可空，避免模型亂填。」
來源 message_id: 45
「風險：日期格式不一，建議先接受字串，不做嚴格 parse。」
來源 message_id: 47
「我們這週里程碑：model/migration/service/api/tests 都已打通。」
來源 message_id: 51
「下週先做前端 snapshot 卡片與 job 狀態輪詢。」
來源 message_id: 52
「風險：群組資料太少時，summary 會偏空。」
來源 message_id: 53
「記得每則訊息都盡量有上下文，AI 比較容易抽出 topics。」
來源 message_id: 56
「大家早，我先把昨天的 endpoint 錯誤碼整理到文件。」
來源 message_id: 57
「如果今天有空，請幫我看一下 action_items 的可讀性。」
來源 message_id: 58
「我發現有些決議句子太短，可能要補前後文。」
來源 message_id: 59
「先決議：本週不引入新依賴，避免部署風險。」
來源 message_id: 60
「今天測了 120 則訊息，snapshot 還在可接受延遲。」
來源 message_id: 63
「如果超過 500 則，背景 job 流程有成功觸發。」
來源 message_id: 64
「大家如果看到摘要有誤，直接貼原始 message id 給我。」
來源 message_id: 68
