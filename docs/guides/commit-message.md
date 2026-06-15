refactor: 正式定版 backend 共用契約層並收尾 Phase 10.2

這次提交把 Phase 10.2 的第一輪後端契約來源收斂正式收尾，重點不是再新增一批 request schema，而是把已經收斂完成的契約層語意正式定版為 `backend/contracts/`，讓 blueprint / service / tool 後續都以這層作為後端共用契約真相來源，同時把相關 README、索引、重構計畫與後續確認文件一併對齊。

---

一、backend 契約層正式搬遷與定版

- 新增：
  - `backend/contracts/README.md`
  - `backend/contracts/__init__.py`
  - `backend/contracts/auth_contracts.py`
  - `backend/contracts/group_contracts.py`
  - `backend/contracts/knowledge_contracts.py`
  - `backend/contracts/profile_contracts.py`
  - `backend/contracts/shared_fields.py`
  - `backend/contracts/task_contracts.py`
  - `backend/contracts/timeline_contracts.py`
  - `backend/contracts/todo_contracts.py`
  - `backend/contracts/tool_envelopes.py`
  - `backend/contracts/tool_inputs.py`
  - `backend/contracts/tool_outputs.py`

- 刪除：
  - `backend/services/contracts/README.md`
  - `backend/services/contracts/__init__.py`
  - `backend/services/contracts/task_contracts.py`
  - `backend/services/contracts/timeline_contracts.py`
  - `backend/services/contracts/tool_envelopes.py`
  - `backend/services/contracts/tool_inputs.py`
  - `backend/services/contracts/tool_outputs.py`

- 本輪收斂重點：
  - 將原本位於 `backend/services/contracts/` 的共用契約層正式搬遷到 `backend/contracts/`
  - 不再把這層視為 service 私有子目錄，而是明確定義為 backend-wide contract layer
  - 後續 blueprint / service / tool 直接以 `backend/contracts/` 作為 schema、envelope 與 shared field 規則的真相來源

---

二、backend import 與責任邊界同步對齊

- 調整：
  - `backend/blueprints/auth.py`
  - `backend/blueprints/groups.py`
  - `backend/blueprints/knowledge.py`
  - `backend/blueprints/profile.py`
  - `backend/blueprints/tasks.py`
  - `backend/blueprints/timelines.py`
  - `backend/blueprints/todos.py`
  - `backend/services/auth_service.py`
  - `backend/services/group_service.py`
  - `backend/services/profile_service.py`
  - `backend/services/task_service.py`
  - `backend/services/timeline_service.py`
  - `backend/services/todo_service.py`
  - `backend/services/tools/error_mapper.py`
  - `backend/services/tools/handlers.py`
  - `backend/services/tools/registry.py`

- 本輪調整內容：
  - 將 backend 內所有 `services.contracts.*` import 改為 `contracts.*`
  - 將 contract 檔案內部對 `shared_fields.py`、task/timeline contract 的引用一併改成新路徑
  - 確保 blueprint / service / tools 這三個主要 consumer 都以同一層共用契約為入口

---

三、README、索引與 Phase 10 文件同步更新

- 調整：
  - `backend/README.md`
  - `backend/services/README.md`
  - `backend/chains/README.md`
  - `docs/reference/backend_契約來源索引.md`
  - `docs/reference/Phase10_2_後端契約收斂實作整理_2026-06-15.md`
  - `docs/reference/Phase10_2_後續確認清單_2026-06-16.md`
  - `docs/future/Future_validation_helper_位置調整評估_2026-06-16.md`
  - `docs/phases/Phase10_2_後端契約來源收斂規劃_2026-06-12.md`
  - `docs/重構計畫.md`
  - `docs/進度追蹤.md`

- 文件收斂重點：
  - 將原本「`services/contracts` 是否要升格為 `backend/contracts`」的討論，正式改成已定案狀態
  - 更新 backend 契約來源索引與 Phase 10.2 實作整理，對齊新的 contract 真相來源位置
  - 將 `validation.py` 保留在 `blueprints/` 的當前結論寫入後續確認清單與 future backlog
  - 將 `10.3` 補成明確的 response contract 收斂起手式，避免後續只修 frontend consumer 而 source of truth 仍鬆散

---

四、Phase 10.2 收尾判定

- 本輪完成後，10.2 可視為已完成的部分：
  - request contract 第一輪收斂
  - contract source index 建立
  - 欄位契約 / 業務規則 / protected fields / route-owned identifiers 邊界定義
  - backend 共用契約層正式定版為 `backend/contracts/`

- 本輪明確不納入的部分：
  - response contract 第二輪收斂
  - mutation / listing / analysis response 的全面命名與 envelope 統一

- 後續銜接：
  - 這部分已明確留給 `10.3` 接續，先做 backend response contract 收斂，再做 frontend type / service 對齊

---

五、驗證

- `python - <<py_compile>>`
  - PASS（本輪搬遷與 import 調整涉及的 backend 檔案皆通過 `py_compile`）
- `venv\\Scripts\\python.exe -m pytest tests/blueprints/test_auth.py tests/blueprints/test_groups.py tests/blueprints/test_knowledge.py tests/blueprints/test_profile.py tests/blueprints/test_tasks.py tests/blueprints/test_timelines.py tests/blueprints/test_todos.py tests/services/test_auth_service.py tests/services/test_group_service.py tests/services/test_profile_service.py tests/services/test_task_service.py tests/services/test_timeline_service_access.py tests/services/test_todo_service.py -q`
  - PASS（`114 passed`，僅 `.pytest_cache` 權限 warning）

---

六、補充

- 這次提交雖然有不少檔案搬移與文件更新，但主題一致，都是為了讓 Phase 10.2 的「後端契約來源收斂」從過渡狀態變成正式結構
- 舊的 phase / learning 文件中若仍保留 `backend/services/contracts/` 路徑，視為當時脈絡紀錄，不作為現行規範入口；現行維護應以 `backend/contracts/` 為主
