# frontend/src

這裡是 Vue 前端主體，負責畫面、互動流程、前端狀態、API 對接與型別整理。

## 目錄分工

- `views/`: 頁面層，通常對應 route
- `components/`: 可重用 UI 區塊與 domain component
- `services/`: 前端 API / socket 呼叫封裝
- `stores/`: Pinia 狀態管理
- `composables/`: 可重用互動邏輯
- `types/`: TypeScript 型別與 domain interface
- `utils/`: 純函式工具與資料轉接 helper
- `router/`: 路由入口與頁面掛載規則
- `styles/`: 第三方樣式或全域樣式資產

## 分層原則

- 頁面進入點放 `views/`
- 可重複使用的畫面區塊放 `components/`
- 對後端怎麼打 API 放 `services/`
- 多頁共用的狀態放 `stores/`
- 不依賴畫面的純工具函式放 `utils/`

## 修改判斷

- 畫面區塊太大、可以獨立測試或重用：先看 `components/`
- 某個頁面的流程與資料組合：先看 `views/`
- API response 要先轉型或映射：先看 `services/` 與 `utils/`
- 欄位型別不清楚或跨檔案重複定義：先看 `types/`
