# frontend/src/views

這層是頁面入口，通常一個檔案對應一個 route。

## 目前頁面

- `HomeView.vue`: 首頁
- `LoginView.vue`, `RegisterView.vue`: 驗證流程
- `TasksView.vue`, `TodosView.vue`, `TrashView.vue`: 任務 / 待辦 / 回收桶
- `GroupsView.vue`: 群組頁
- `TimelinesView.vue`: timeline 主頁
- `KnowledgeBaseView.vue`: 知識庫頁
- `ProfileView.vue`: 個人資料頁

## 這層應該負責什麼

- 頁面層資料載入
- route 對應的組件組裝
- 頁面層級的 UI 狀態協調

## 不應該放什麼

- 大量可重用子區塊的細節 template
- 重複出現的 API 呼叫樣板
- 純工具函式

## 修改判斷

- 整頁行為、頁面切換、頁面層資料流：改這裡
- 局部區塊可獨立理解：優先拆去 `components/`
