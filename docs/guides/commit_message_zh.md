refactor(frontend): 完成 Phase 8.4 大型視圖元件拆分與編排層收斂

## 這次做了什麼

### 1) TimelineDetailDialog 大型區塊拆分
- 拆出 `ProjectKnowledgePanel.vue`（專案檔案區）
- 拆出 `AiTaskGeneratePanel.vue`（AI 生成任務流程）
- 拆出 `TaskDetailPanel.vue`（任務詳情內容區）
- `TimelineDetailDialog.vue` 保留為流程編排與狀態協調層，透過 `props/emits` 與子元件互動

### 2) TimelineViewModes 大型視圖拆分
- 拆出 `TimelineListView.vue`
- 拆出 `TimelineCalendarView.vue`
- 拆出 `TimelineCardView.vue`
- 拆出 `TimelineKanbanBoard.vue`
- 拆出 `TimelineKanbanTaskModal.vue`
- 拆出 `TimelineGanttView.vue`
- `TimelineViewModes.vue` 收斂為「視圖切換 + 行為編排」主殼層

### 3) Gantt 區塊收斂
- Gantt UI 與控制列移入 `TimelineGanttView.vue`
- 父層維持 gantt instance/render/update 的流程與資料來源
- 新增 `setGanttContainerRef` 將容器 ref 經由 props 傳遞，維持現有渲染邏輯

### 4) 文件同步（root + docs）
- 更新 `重構計畫.md`：8.4 標記為核心完成
- 更新 `進度追蹤.md`：本期焦點改為 8.5+，同步 8.4 完成狀態
- 同步更新 `docs/重構計畫.md`、`docs/進度追蹤.md`

## 驗證
- `npm run build`（多輪）通過
- `npm run test -- TimelineDetailDialog.phase7.test.ts timelineService.test.ts` 通過（2 files / 6 tests）

## 為什麼要這樣改
- 降低單檔責任密度，避免 `TimelineDetailDialog.vue` / `TimelineViewModes.vue` 持續膨脹
- 提升可維護性：後續改動可局部落在對應子元件
- 維持行為不變：本次以結構重構為主，不改 API 契約與產品流程

## 影響範圍
- 前端 timelines 相關元件結構重整
- 無後端 API 契約變更
- 無部署流程變更
