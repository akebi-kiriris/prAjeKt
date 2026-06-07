# 後端 Transaction 重構順序_2026-05-15

## 目標

逐步收斂 service 層散落的 `db.session.commit()` / `db.session.rollback()`，讓 transaction 邊界更清楚，後續再視需要演進成 Unit of Work。

原則：

- 不把 `commit()` 放進 repository。
- 不一次機械式替換所有 `commit()`。
- 單段資料變更優先改成 `with transaction(...)`。
- 有狀態流轉的流程先拆成語意明確的小段落。

## 第一波：建立共用 transaction helper

狀態：已完成。

內容：

- 新增 `backend/services/transactions.py`。
- 新增 `transaction(error_cls, error_message, status_code=500)`。
- 將 knowledge service 中幾個單段交易改成 `with transaction(...)`：
  - `delete_knowledge_document()`
  - `batch_reindex_knowledge_documents()` 中額外建立 reindex event 的交易
  - `get_project_knowledge_document_file()` 中建立 download / preview event 的交易
- 修正 `backend/blueprints/knowledge.py` 中 `error_response` 變數遮蔽 bug。
- 補上 batch delete / batch reindex 空 `document_ids` 測試。

驗證：

```bash
.\venv\Scripts\python.exe -m pytest tests/services/test_knowledge_service.py tests/blueprints/test_knowledge.py
```

結果：

```text
6 passed
```

## 第二波：整理 knowledge upload / reindex 狀態流程

狀態：已完成。

內容：

- 精簡本文件，改為只追蹤「第幾波做了哪些事」。
- 整理 `upload_and_index_knowledge_document()` 的狀態流程。
- 整理 `reindex_knowledge_document()` 的狀態流程。
- 新增 knowledge service 內部 helper：
  - `_create_uploaded_document()`
  - `_mark_document_indexing()`
  - `_mark_document_indexing_by_id()`
  - `_build_chunk_rows()`
  - `_replace_chunks_and_mark_ready()`
  - `_replace_chunks_and_mark_ready_by_id()`
  - `_mark_document_failed()`
  - `_mark_document_failed_by_id()`
  - `_record_project_document_event()`
- 讓 `knowledge_service.py` 不再直接使用 `db.session.commit()` / `db.session.rollback()`。

保留設計：

- 沒有把整個 upload / reindex 流程包成單一大 transaction。
- 每個狀態轉換各自有明確交易邊界。
- 保留 `uploaded -> indexing -> ready/failed` 的可觀察狀態。

驗證：

```bash
.\venv\Scripts\python.exe -m pytest tests/services/test_knowledge_service.py tests/blueprints/test_knowledge.py
```

結果：

```text
6 passed
```

## 第三波：推廣到 task / timeline 既有 commit helper

狀態：已完成。

內容：

- 移除 `task_service.py` 的 `_commit_or_raise_task_error()`。
- 移除 `timeline_service.py` 的 `_commit_or_raise_timeline_error()`。
- 在 `task_service.py` 導入 `transaction()`，並改寫原本使用 task commit helper 的單段 mutation：
  - 任務更新
  - 任務軟刪除
  - 任務完成狀態切換
  - 留言軟刪除
  - 子任務新增 / 更新 / 刪除 / 切換
  - 任務狀態更新
  - 任務檔案刪除
- 在 `timeline_service.py` 導入 `transaction()`，並改寫原本使用 timeline commit helper 的單段 mutation：
  - 專案更新
  - 專案軟刪除
  - 專案備註更新
  - 專案成員移除
- 補強 `transaction()`，遇到既有 operation error 時會 rollback 後原樣拋出，不會誤包成 500。

保留設計：

- 暫不處理 task / timeline 中較大的多步驟流程，例如建立任務、成員新增、檔案上傳、AI 批次建立任務。
- 這些流程後續應該依 use case 語意分段整理，不做機械式替換。

驗證：

```bash
.\venv\Scripts\python.exe -m pytest tests/services/test_task_service.py tests/services/test_timeline_service_access.py tests/services/test_timeline_service_conflicts.py tests/services/test_timeline_service_reporting.py tests/services/test_timeline_service_ai.py tests/services/test_knowledge_service.py tests/blueprints/test_knowledge.py
```

結果：

```text
43 passed
```

## 第四波：收斂 task / timeline 剩餘單段 DB transaction

狀態：已完成。

內容：

- 繼續降低 service 裡直接手寫 `db.session.commit()` / `db.session.rollback()` 的數量。
- 將 task / timeline 中沒有檔案 IO、沒有 AI 批次流程、沒有複雜狀態流轉的單段 DB 寫入改成 `with transaction(...)`。
- 已處理 `task_service.py`：
  - `add_task_member_for_operator()`
  - `remove_task_member_for_owner()`
  - `update_task_member_role_for_operator()`
  - `add_task_comment_for_member()`
- 已處理 `timeline_service.py`：
  - `create_timeline_for_user()`
  - `trigger_timeline_risk_notifications()`
  - `add_timeline_member_for_owner()`

保留設計：

- `create_task_for_user()` 保留到大型流程重排。
- `upload_task_file_for_member()` 保留到檔案 IO + DB 混合流程。
- `batch_create_tasks_for_timeline()` 保留到大型流程重排。

驗證：

```bash
.\venv\Scripts\python.exe -m pytest tests/services/test_task_service.py tests/services/test_timeline_service_access.py tests/services/test_timeline_service_conflicts.py tests/services/test_timeline_service_reporting.py tests/services/test_timeline_service_ai.py tests/services/test_knowledge_service.py tests/blueprints/test_knowledge.py
```

結果：

```text
43 passed
```

## 第五波：整理檔案 IO + DB 混合流程

狀態：已完成。

內容：

- 整理 `task_service.py` 的 task file 實體檔案流程。
- 新增檔案清理 helper：
  - `_remove_file_if_exists()`
  - `_cleanup_task_upload_files()`
- 將 `upload_task_file_for_member()` 的 DB 寫入改成 `with transaction(...)`。
- 移除上傳失敗時對 rollback 後 `task_file` 再 `delete + commit` 的多餘補償。
- 補強 task file 測試，驗證：
  - 上傳後實體檔案存在。
  - 刪除後 DB record 消失。
  - 刪除後實體檔案也消失。

保留設計：

- `delete_task_file_for_user()` 已在第三波使用 `transaction()` 處理 DB delete，這波只集中清理檔案刪除 helper 與測試確認。
- knowledge project file 流程目前已由第二波整理過，暫不追加改動。

驗證：

```bash
.\venv\Scripts\python.exe -m pytest tests/services/test_task_service.py tests/services/test_timeline_service_access.py tests/services/test_timeline_service_conflicts.py tests/services/test_timeline_service_reporting.py tests/services/test_timeline_service_ai.py tests/services/test_knowledge_service.py tests/blueprints/test_knowledge.py
```

結果：

```text
43 passed
```

## 第六波：重排 create_task_for_user()

狀態：已完成。

內容：

- 將 `create_task_for_user()` 中混在一起的驗證、payload 正規化、DB 寫入與通知建立拆開。
- 新增 task 建立流程 helper：
  - `_build_task_create_payload()`
  - `_validate_task_create_membership()`
  - `_create_task_with_members_and_notifications()`
- 將任務建立、owner 成員建立、被指派成員建立、通知建立包進單一 `with transaction(...)`。
- 讓 `task_service.py` 不再直接使用 `db.session.commit()` / `db.session.rollback()`。

保留設計：

- `create_task_for_user()` 仍保留 application service orchestration 角色。
- 這波先不急著把 `Task(...)`、`TaskUser(...)`、`Notification(...)` entity 建構移出 service；先把交易邊界收乾淨。

驗證：

```bash
.\venv\Scripts\python.exe -m pytest tests/services/test_task_service.py tests/services/test_timeline_service_access.py tests/services/test_timeline_service_conflicts.py tests/services/test_timeline_service_reporting.py tests/services/test_timeline_service_ai.py tests/services/test_knowledge_service.py tests/blueprints/test_knowledge.py
```

結果：

```text
43 passed
```

## 第七波：重排 batch_create_tasks_for_timeline()

狀態：已完成。

內容：

- 將 `batch_create_tasks_for_timeline()` 的手動 `try/commit/rollback` 改為 `with transaction(...)`。
- 保留原有流程語意（舊任務保留/刪除、新任務建立、依賴關係解析與忽略計數）。
- 主線 `knowledge_service.py` / `task_service.py` / `timeline_service.py` 已無直接 `db.session.commit()` / `db.session.rollback()`。

保留設計：

- 這波先集中在 transaction 邊界收斂，不同時大改函式責任切分。
- `batch_create_tasks_for_timeline()` 內部仍有 entity 建構與 `db.session.add()/flush()`，留到下一波抽象化。

驗證：

```bash
.\venv\Scripts\python.exe -m pytest tests/services/test_timeline_service_ai.py
```

結果：

```text
6 passed
```

原範圍：

- `batch_create_tasks_for_timeline()`
- timeline AI 產生任務後批次寫入。

## 第八波：抽出建立類 use case 的 ORM entity 建構

狀態：已完成。

目標：

- 降低 service 直接知道 `Task(...)`、`Timeline(...)`、`Notification(...)`、`TaskUser(...)` 細節的程度。
- 評估放到 repository helper 或 factory helper。

預計範圍：

- `create_task(...)`
- `create_task_member(...)`
- `create_notification(...)`
- `create_timeline_with_owner(...)`

內容：

- 新增共用 session helper：
  - `session_repository.py`
  - `add_entity()`
  - `flush_session()`
- `task_repository.py` 新增建立類 helper：
  - `build_task_entity()`
  - `build_task_member_entity()`
  - `build_notification_entity()`
- `timeline_repository.py` 新增建立類 helper：
  - `build_timeline_task_entity()`
  - `build_timeline_entity()`
  - `build_timeline_member_entity()`
- `task_service.py` 的 `create_task_for_user()` / `create_notification()` 改為使用 repository 建構 helper + 共用 session helper。
- `timeline_service.py` 的 `batch_create_tasks_for_timeline()` / `create_timeline_for_user()` 改為使用 repository 建構 helper + 共用 session helper。
- 統一移除 repository 間重複的 `add_task_entity()/flush_session()` 入口，避免雙軌 API。

驗證：

```bash
.\venv\Scripts\python.exe -m pytest tests/services/test_task_service.py tests/services/test_timeline_service_ai.py tests/services/test_timeline_service_access.py tests/services/test_timeline_service_conflicts.py tests/services/test_timeline_service_reporting.py
```

結果：

```text
37 passed
```

## 第九波：收斂剩餘 service transaction

狀態：已完成。

內容：

- 將剩餘 service 內的 `db.session.commit()` / `db.session.rollback()` 收斂為 `with transaction(...)`。
- 已處理：
  - `group_service.py`
  - `todo_service.py`
  - `trash_service.py`
  - `profile_service.py`
  - `auth_service.py`（保留 `IntegrityError -> 409` 映射）
  - `message_service.py`
  - `notification_service.py`
  - `text_splitter_service.py`（failed 補償路徑改為 transaction，且不覆蓋原始錯誤）
- `notifications` blueprint 的 `read-all` 補上 `NotificationOperationError` 轉譯。

驗證：

```bash
.\venv\Scripts\python.exe -m pytest tests/services/test_auth_service.py tests/blueprints/test_auth.py tests/services/test_group_service.py tests/services/test_group_snapshot.py tests/blueprints/test_groups.py tests/services/test_todo_service.py tests/blueprints/test_todos.py tests/services/test_trash_service.py tests/blueprints/test_trash.py tests/services/test_message_service.py tests/blueprints/test_messages.py tests/services/test_notification_service.py tests/blueprints/test_notifications.py tests/services/test_profile_service.py tests/blueprints/test_profile.py tests/services/test_text_splitter_service.py
```

結果：

```text
80 passed
```

## 第十波：統一 service session 操作入口（add/flush/delete）

狀態：已完成。

內容：

- `session_repository.py` 新增 `delete_entity()`，與既有 `add_entity()` / `flush_session()` 統一為 session 操作入口。
- 將 service 層剩餘 `db.session.add()` / `db.session.flush()` / `db.session.delete()` 全部收斂為共用 helper 呼叫。
- `backend/services` 主線僅 `transactions.py` 保留 `commit/rollback`（符合 transaction helper 單一責任）。

驗證：

```bash
.\venv\Scripts\python.exe -m pytest tests/services/test_group_service.py tests/services/test_group_snapshot.py tests/blueprints/test_groups.py tests/services/test_task_service.py tests/services/test_timeline_service_access.py tests/services/test_timeline_service_conflicts.py tests/services/test_timeline_service_reporting.py tests/services/test_timeline_service_ai.py tests/services/test_trash_service.py tests/blueprints/test_trash.py tests/services/test_notification_service.py tests/blueprints/test_notifications.py
```

結果：

```text
74 passed
```

## 第十一波：導入 repository 語意化 helper（漸進式）

狀態：未開始。

目標：

- 在不導入完整 UoW 的前提下，降低 service 對「多步驟 persistence 細節」的認知負擔。
- 讓高變動 use case 優先收斂為語意化入口，避免繼續堆疊通用 helper 呼叫細節。

建議範圍（先高價值區）：

- `timeline_service.py`：成員加入/移除與通知聯動流程（member + notification）
- `task_service.py`：成員角色流轉與通知聯動流程（task_member + role demotion + notification）
- `group_service.py`：建立群組 + owner membership 初始化流程

建議策略：

- 保留通用 `add_entity()/flush_session()/delete_entity()` 作為底層能力。
- 僅在「重複出現、規則複雜、跨多 entity」流程新增語意化 helper，例如：
  - `add_timeline_member_with_invite_notification(...)`
  - `transfer_task_owner_and_demote_previous(...)`
  - `create_group_with_owner_member(...)`
- 單筆 CRUD 不強制語意化，避免過度抽象。

完成標準：

- 不改變 API 契約與錯誤碼語意。
- 主要 service 函式可讀性提升（流程語意優先，session 細節更少）。
- 既有回歸測試保持綠燈。

## 第十二波：評估是否需要 Unit of Work

狀態：未開始。

觸發條件：

- 多個 repository 操作越來越難組合。
- service 測試仍需大量依賴 SQLAlchemy session。
- transaction 邊界需要更明確的 application service pattern。

目前先不急著導入完整 Unit of Work。
