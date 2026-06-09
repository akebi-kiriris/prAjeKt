refactor: 拆分 timeline detail dialog 並同步收斂前端入口與文件

這次提交主要收斂第三波前端結構清理，重點是把 `TimelineDetailDialog.vue` 內責任較獨立的區塊持續拆出，讓主元件回到 orchestration 角色，而不是繼續累積為單一巨型元件；同時同步前端入口描述與重構文件，作為銜接 Phase 9.6 前的整理提交。

---

一、TimelineDetailDialog 再拆分

- 新增以下子元件：
  - `frontend/src/components/timelines/TimelineAddTaskModal.vue`
  - `frontend/src/components/timelines/TimelineSharePanel.vue`
  - `frontend/src/components/timelines/TimelineTaskMemberPanel.vue`
  - `frontend/src/components/timelines/TimelineWeeklyReportPanel.vue`
  - `frontend/src/components/timelines/TimelineRiskAnalysisPanel.vue`

- `TimelineDetailDialog.vue` 保留：
  - service 呼叫
  - 權限判斷
  - toast / confirm
  - refresh 與整體流程編排

- 子元件只承接：
  - UI 呈現
  - 表單輸入
  - emit 事件回拋

- 量化結果：
  - `TimelineDetailDialog.vue`
  - `2152 -> 1637` 行
  - 累計減少 `515` 行

---

二、前端入口收斂

- 正式完成前端入口 TS 化與引用更新：
  - `frontend/src/main.ts`
  - `frontend/src/router/index.ts`
  - `frontend/index.html` 改為引用 `/src/main.ts`

---

三、文件同步

- 更新 `docs/重構計畫.md`
  - 補上第三波 Timeline 結構清理結果
  - 更新 `main.ts` / `router/index.ts` 目標結構描述
  - 同步目前 Timeline 區的剩餘技術債狀態

- 更新 `docs/進度追蹤.md`
  - 補上 `2026/06/10` 第三波 Timeline 結構清理里程碑
  - 同步目前 Phase 9 / Timeline 區的最新狀態

---

四、驗證

- `npm run build`
  - PASS

- `npm run test -- TimelineDetailDialog.phase7.test.ts TimelineSubcomponents.test.ts TimelineViewModes.test.ts`
  - `27 passed`

---

五、補充

- 本次重點是前端責任拆分與結構收斂，不新增產品功能
- `TimelineViewModes.vue` 與 `TimelineDetailDialog.vue` 主體仍偏大，但已先完成第三波的第一段與第二段收斂
- 這次提交可視為進入 Phase 9.6 前的前端結構整理基線，下一步較適合轉向可觀測性、benchmark 與 Agent/tooling 擴充
