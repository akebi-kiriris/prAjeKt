# frontend/src/components/timelines

這裡是 timeline domain 的主要 UI 區塊，包含專案檢視模式、詳情對話框，以及週報、風險分析、知識面板等子區塊。

## 常見元件角色

- `TimelineDetailDialog.vue`: timeline 詳情的主要容器，負責整合多個 panel
- `TimelineWeeklyReportPanel.vue`: 週報區塊
- `TimelineRiskAnalysisPanel.vue`: 風險分析與圖表區塊
- `ProjectKnowledgePanel.vue`: 專案知識相關區塊
- `TimelineListView.vue` / `TimelineCardView.vue` / `TimelineCalendarView.vue` / `TimelineGanttView.vue` / `TimelineKanbanBoard.vue`: 各種 timeline 檢視模式
- `TimelineAddTaskModal.vue` / `TimelineKanbanTaskModal.vue`: 任務建立或編輯互動

## 拆分原則

- 容器元件保留資料整合、狀態協調、事件串接
- 子面板元件負責單一區塊的展示與局部互動
- 若某段邏輯與畫面只服務一個 panel，優先留在該 panel，不必急著抽成全域 composable

## 避免長回史山的做法

- 不把每個 panel 的 loading / error / empty state 全塞回主 dialog
- 不把 risk / weekly report / knowledge 的細節 formatter 都混在同一支檔案
- 拆出來的元件要有清楚名稱與責任，不要只是為了切行數而硬拆
