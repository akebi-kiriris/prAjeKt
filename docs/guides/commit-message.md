test: 完成 Phase 11 前端測試基線與 Agent payload 修正

這次提交完成 Phase 11 前端測試補強與專案健檢，將前端型別檢查、coverage、核心元件互動、錯誤邊界、Socket 狀態與 Browser smoke test 收斂成可持續重跑的驗證基線。同時補上一個 Agent tool chaining 的 payload 修正，避免 AI 生成任務的 response-only 欄位流入 batch create tool。

---

一、Phase 11 前端測試與 CI 基線

- 新增 Phase 11 規劃文件：
  - `docs/phases/Phase11_前端測試補強與專案健檢規劃_2026-06-24.md`

- 更新 roadmap 與追蹤文件：
  - `docs/重構計畫.md`
  - `docs/進度追蹤.md`
  - `docs/phases/Phase9_6_Agent可觀測性與評測基線規劃_2026-06-02.md`
  - `docs/phases/Phase10_契約收斂與前後端對齊規劃_2026-06-12.md`
  - `docs/phases/Phase10_6_已知鬆動點實作清理規劃_2026-06-18.md`

- Phase 編號調整：
  - Phase 11：前端測試補強與專案健檢
  - Phase 12：Integration Test
  - Phase 13：Evaluation
  - Phase 14：Observability

- 前端驗證入口：
  - 新增 `npm run type-check`
  - CI 加入 type-check
  - coverage 納入主要 frontend source
  - coverage 排除純型別、啟動點與 router 噪音
  - thresholds 提高為 Statements `74%`、Branches `68%`、Functions `72%`、Lines `77%`

---

二、前端核心流程與錯誤邊界測試

- 新增與擴充測試：
  - Header 通知中心、未讀篩選、導頁與登出
  - ConfirmDialog 確認、取消與 danger 狀態
  - Login / Register 成功、失敗、token 保存與登出
  - Home / Profile / Todos / Trash 基礎 smoke 與主要互動
  - TasksView 搜尋、篩選、排序、指派、邀請協作者與 API 失敗
  - TimelinesView 基礎 render 與入口 smoke
  - TimelineDetailDialog 任務詳情、成員管理、AI 衝突建議與指派衝突
  - Timeline view modes、Gantt、Kanban 與成員 panel 邊界
  - GroupsView 群組互動、快照錯誤訊息與 messages fallback
  - CopilotDock plan、replan、execute、reject 與錯誤狀態
  - `auth` / `groups` stores
  - `apiError`、`taskDetails`、`timelineDetailUtils` 純工具函式

- 產品碼修正：
  - Timeline AI 衝突建議在未填截止日期時，先顯示 warning，再避免 mapper 提前拋錯
  - Tasks / Todos / Groups / Timeline 子元件補齊測試所暴露的錯誤狀態與資料邊界

---

三、Copilot、Socket 與 Timeline 最後錯誤邊界

- CopilotDock：
  - 規劃 API 失敗後保留輸入並結束 loading
  - 重提案失敗後保留原 plan
  - 執行失敗後不產生假的成功結果
  - 放棄計畫失敗後不清空目前 plan
  - malformed step output 不造成 render crash 或 `undefined` 文案

- groups store Socket：
  - 無 token 時不建立 Socket 連線
  - 重複訊息去重
  - 其他群組訊息不污染目前 state
  - connect / disconnect / ready / error 狀態可預期
  - destroy socket 時清理 handler 與狀態

- TimelineDetailDialog：
  - AI 衝突建議失敗後保留 conflict preview
  - 未填截止日期時不呼叫 conflict API
  - 無成員管理權限時不顯示指派入口
  - 指派衝突檢查失敗時不產生副作用

---

四、Agent generated task payload 修正

- 調整：
  - `backend/chains/agent_nodes.py`
    - 新增 generated task → batch create item 的 narrow normalization
    - 只保留 batch create tool 允許的欄位
    - 移除 `timeline_id`、`completed`、未知欄位等 response-only data

- 新增測試：
  - `backend/tests/chains/test_agent_graph.py`
    - 驗證 `generate_timeline_tasks_with_ai` 的 output 餵給 `batch_create_tasks_for_timeline` 前會移除 response-only fields

- 保留原則：
  - 不放寬 batch create input contract
  - 不把 response-only 欄位默默交給 service
  - 長期 adapter 抽出先記錄到 future backlog，不在本次擴張重構

---

五、Future backlog 整理

- 新增：
  - `docs/future/Future_Agent工具PayloadAdapter與契約映射整理_2026-06-29.md`
  - `docs/future/Future_magic_numbers_與設定常數盤點_2026-06-29.md`

- 更新：
  - `docs/future/README.md`

- 記錄重點：
  - tool-to-tool payload mapping 未來可抽成 payload adapter
  - `agent_nodes.py` 短期可放 narrow normalization，但不應長期累積所有 tool-specific mapping
  - magic numbers / hard-coded limits 後續應區分 business rule、config、UI display、test fixture 與文件範例

---

六、依賴與型別檢查整理

- `frontend/package.json`：
  - 新增 `vue-tsc`
  - 新增 `type-check` script
  - 更新 Vite / PostCSS / Axios 相關版本
  - 移除目前 frontend source 未使用的 Firebase dependency

- `frontend/tsconfig.json`：
  - 加入 `skipLibCheck`

- `backend/tests/conftest.py`：
  - teardown 時 dispose engine，降低測試資源殘留

---

七、驗證

- Frontend focused tests：
  - `CopilotDock.test.ts`：`11 passed`
  - `groups.test.ts`：`10 passed`
  - `TimelineDetailDialog.phase7.test.ts`：`13 passed`
  - 合併 focused tests：`3 test files / 34 tests passed`

- Frontend full checks：
  - `npm run test:coverage`：`46 test files / 283 tests passed`
  - Coverage：
    - Statements `81.09%`
    - Branches `74.71%`
    - Functions `78.49%`
    - Lines `84.30%`
  - `npm run type-check`：PASS
  - `npm run build`：PASS
  - `npm run guardrails:payload`：PASS

- Browser smoke：
  - standalone Playwright + 本機 Chrome
  - Login、Home、Tasks、Timelines、Groups、Profile、Todos、Trash
  - Desktop `1440x900`、Mobile `390x844`
  - 無空白頁、Vite overlay、console warning / error

- Agent focused backend test：
  - `python -m pytest tests/chains/test_agent_graph.py -q`
  - `22 passed`
  - 僅 `.pytest_cache` 權限 warning，不影響結果

- Git diff check：
  - `git diff --check`：PASS
  - 僅 Windows LF/CRLF 提示

---

八、補充

- `docs/learning/前端型別檢查與專案健檢改善紀錄.md` 仍屬本機學習紀錄，位於 `.gitignore` 的 `/docs/learning/**` 範圍，未納入本次一般 commit
- Phase 11 已可正式結案，後續跨 frontend / backend / database / Agent 的真實流程驗證歸入 Phase 12 Integration Test
