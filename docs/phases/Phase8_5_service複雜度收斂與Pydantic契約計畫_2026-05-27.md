# Phase 8.5：Service 複雜度收斂與 Pydantic 契約計畫

> 日期：2026-05-27  
> 範圍：`backend/services/timeline_service.py`、`backend/services/task_service.py`  
> 目標：在不改動 API 契約與前端行為前提下，降低 service 複雜度、補齊內部輸入輸出契約（Pydantic）

---

## 1. 背景與目標

Phase 8.4 已完成前端大型元件拆分，8.5 進入後端 service 可維護性收斂。  
目前 `timeline_service.py` / `task_service.py` 單檔函式數與責任密度偏高，雖可用但維護與變更成本高。

本階段目標：

1. 將高重複邏輯抽為 helper，提升主流程可讀性。
2. 將 service 內部關鍵 I/O 轉為 Pydantic model，建立穩定契約。
3. 保持外部 API 回應結構與錯誤碼不變。
4. 以小步可回滾方式落地，每波都可驗證。

---

## 2. 不做事項（避免過度擴張）

1. 不在本階段導入完整 UoW/AbstractRepository。
2. 不重寫 blueprint 層對外 payload 契約。
3. 不一次全檔 Pydantic 化（採主路徑優先）。
4. 不改變既有錯誤碼語義與 HTTP status。

---

## 3. 交付成果定義

完成 8.5 視為達標需同時滿足：

1. `timeline_service.py`、`task_service.py` 主流程已可讀（流程骨架清楚，細節下沉）。
2. 至少 3 條高價值主路徑完成 Pydantic 內部契約化。
3. 聚焦測試 + 全量核心回歸綠燈。
4. 文件（重構計畫/進度追蹤）同步更新。

---

## 4. 實作策略（Helper + Pydantic）

### 4.1 Helper 原則

1. 抽「可命名步驟」而非機械拆行。
2. 優先抽重複出現的驗證/正規化/組裝邏輯。
3. 主流程函式保留 20~40 行可閱讀骨架（validate -> load -> execute -> map response）。

### 4.2 Pydantic 使用原則

1. Pydantic 主要用於 service 內部進出契約，不直接變更外部 API schema。
2. Blueprint 進來後，可先 `model_validate(...)`，service 吃 model；回傳前 `model_dump(...)`。
3. 高頻、極簡資料可暫時保留 `TypedDict`，避免過度儀式化。

### 4.3 模型放置建議

新增：

- `backend/services/contracts/timeline_contracts.py`
- `backend/services/contracts/task_contracts.py`

範例模型（第一波）：

1. `ConflictCheckInput`
2. `ConflictCheckResult`
3. `WeeklyReportInput`
4. `WeeklyReportSummary`
5. `TaskCreateInput`
6. `TaskUpdateInput`

---

## 5. 分波計畫（建議 4 波）

## Wave 1：Timeline 核心流程收斂（低風險）

目標檔案：

- `backend/services/timeline_service.py`

優先路徑：

1. `build_weekly_report_for_timeline(...)`
2. `check_timeline_task_conflicts(...)`
3. `batch_create_tasks_for_timeline(...)`

本波動作：

1. 抽 helper（示例命名）
 - `_validate_weekly_report_input(...)`
 - `_collect_weekly_report_sources(...)`
 - `_build_weekly_report_response(...)`
 - `_validate_conflict_payload(...)`
 - `_build_conflict_response(...)`
2. 引入 Pydantic
 - WeeklyReportInput / ConflictCheckInput / ConflictCheckResult
3. 不改資料來源與 repository 呼叫順序。

本波驗證：

```powershell
cd backend
venv\Scripts\python.exe -m pytest tests/services/test_timeline_service_reporting.py tests/services/test_timeline_service_conflicts.py tests/services/test_timeline_service_ai.py
```

---

## Wave 2：Task 主路徑收斂（中風險）

目標檔案：

- `backend/services/task_service.py`

優先路徑：

1. `create_task_for_user(...)`
2. `update_task_for_member(...)`
3. `update_task_status_for_member(...)`

本波動作：

1. 抽 helper（示例命名）
 - `_validate_task_create_input(...)`
 - `_prepare_task_create_payload(...)`
 - `_apply_task_update_payload(...)`
 - `_validate_status_transition(...)`
2. 引入 Pydantic
 - TaskCreateInput / TaskUpdateInput / TaskStatusUpdateInput
3. 保留既有 `TaskOperationError` 與 error_code 行為。

本波驗證：

```powershell
cd backend
venv\Scripts\python.exe -m pytest tests/services/test_task_service.py tests/services/test_task_service_serializers.py tests/blueprints/test_tasks.py
```

---

## Wave 3：留言/子任務/檔案路徑收斂（中風險）

目標檔案：

- `backend/services/task_service.py`

優先路徑：

1. comment summary 相關
2. subtask CRUD
3. file upload/download/delete

本波動作：

1. 抽 helper（示例命名）
 - `_load_task_comment_context(...)`
 - `_validate_subtask_input(...)`
 - `_build_file_upload_result(...)`
2. Pydantic 化 summary input/output（先內部）。
3. 保持檔案刪除/清理語義不變（先 DB 後檔案清理）。

本波驗證：

```powershell
cd backend
venv\Scripts\python.exe -m pytest tests/services/test_task_service.py tests/blueprints/test_tasks.py
```

---

## Wave 4：收尾與一致性清理（低風險）

目標：

1. 命名與註解一致化（helper 命名、型別別名）。
2. 刪除已失效的舊 helper/重複 normalizer。
3. 補齊文件與進度標記。

本波驗證：

```powershell
cd backend
venv\Scripts\python.exe -m pytest
```

---

## 6. 風險與對策

### 風險 A：Pydantic 導入後錯誤訊息改變

對策：

1. service 捕捉 validation error，映射回既有 `TaskOperationError` / `TimelineOperationError`。
2. 不把原生 Pydantic error 直接透出 blueprint。

### 風險 B：helper 拆分導致流程順序錯置

對策：

1. 每波只改 1~3 條主路徑。
2. 每次重構先保留原流程註解與 checkpoint commit。

### 風險 C：過度拆分

對策：

1. helper 只抽可命名業務步驟。
2. 小於 3~5 行且不重複片段不拆。

---

## 7. 命名規範（本階段）

1. 驗證：`_validate_xxx`
2. 正規化：`_normalize_xxx`
3. 組裝：`_build_xxx`
4. 載入：`_load_xxx`
5. Pydantic model：
 - Input：`XxxInput`
 - Result/Response：`XxxResult` / `XxxSummary`

---

## 8. 執行順序建議（你可直接照這個走）

1. 先做 Wave 1（timeline reporting/conflict）
2. 再做 Wave 2（task create/update/status）
3. 然後 Wave 3（comment/subtask/file）
4. 最後 Wave 4（一致性與文件）

---

## 9. 完成後文件同步清單

1. `重構計畫.md` 更新 8.5 子項狀態
2. `進度追蹤.md` 更新本期焦點
3. `docs/重構計畫.md`、`docs/進度追蹤.md` 同步

---

## 10. 你可以先確認的決策點

1. Pydantic contracts 檔案位置是否採 `backend/services/contracts/`
2. Wave 1 是否優先 `weekly_report + conflict`（我建議是）
3. 錯誤映射策略是否維持現有 operation error 為唯一出口（我建議維持）
4. 每波是否都要先做聚焦測試再做全量（我建議是）
