refactor: 抽離 tool planner prompt 並補齊前後端分層 README

這次提交的重點不是新增功能，而是把 Phase 10 前置整理真正落到 repo 裡：一方面把 `tool_plan_service.py` 內嵌的 planner prompt 抽回 `backend/prompts/`，讓 prompt 集中管理；另一方面補齊前後端多個關鍵目錄的 README，讓 prompt、contracts、tools、types、utils、services、tests 的責任邊界更清楚。

---

一、tool planner prompt 抽離

- 新增：
  - `backend/prompts/tool_planner.py`

- 調整：
  - `backend/services/tool_plan_service.py`
  - `backend/prompts/__init__.py`

- 本輪收斂方式：
  - 將固定 planner 規則抽成 `TOOL_PLANNER_SYSTEM_PROMPT`
  - 以 `build_tool_planner_prompt(...)` 組裝 `user_message`、`context`、`tool_lines`、`protected_payload_keys`
  - 讓 `tool_plan_service.py` 回到 orchestration / proposal parsing 角色，不再自己維護大段 prompt 字串

---

二、README / 分層規範補齊

- backend 補強：
  - `backend/prompts/README.md`
  - `backend/services/contracts/README.md`
  - `backend/services/tools/README.md`

- frontend / repo 補齊：
  - `frontend/src/README.md`
  - `frontend/src/components/README.md`
  - `frontend/src/components/timelines/README.md`
  - `frontend/src/components/__tests__/README.md`
  - `frontend/src/composables/README.md`
  - `frontend/src/router/README.md`
  - `frontend/src/services/README.md`
  - `frontend/src/stores/README.md`
  - `frontend/src/styles/README.md`
  - `frontend/src/types/README.md`
  - `frontend/src/utils/README.md`
  - `frontend/src/views/README.md`
  - `scripts/README.md`

- 本輪補強重點：
  - prompt 的 `PromptTemplate` / builder helper 分界
  - agent `contracts -> tools -> services` 的責任切法
  - frontend `types -> utils -> services -> components/__tests__` 的契約與測試分界

---

三、文件同步

- 更新：
  - `docs/重構計畫.md`
  - `docs/進度追蹤.md`

- 同步內容：
  - 補上 `2026/06/11` 這波 Phase 10 前置收斂紀錄
  - 將進度追蹤的當前 Phase 切到 Phase 10 視角
  - 把「prompt 抽離 + README 規範補齊」記錄為 9.6 前的理解與邊界整理基線

---

四、驗證

- `python -m py_compile backend\prompts\tool_planner.py backend\prompts\__init__.py backend\services\tool_plan_service.py`
  - PASS

---

五、補充

- 本次重點是結構理解、責任邊界與 prompt 管理收斂，不新增產品功能
- 這次提交可視為 Phase 10 的第一輪 repo 釐清，幫後續 9.6、11~13 的實作先把規範面補齊
