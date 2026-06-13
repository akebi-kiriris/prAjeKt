# Frontend Src 目錄說明

`frontend/src/` 是 Vue 前端主體，負責畫面呈現、互動流程、前端狀態、API 對接與型別整理。

## 目錄分工

1. `views/`
   - 頁面層，通常對應 route。
2. `components/`
   - 可重用 UI 區塊與 domain component。
3. `services/`
   - 前端 API 與 socket 呼叫封裝。
4. `stores/`
   - Pinia 狀態管理。
5. `composables/`
   - 可重用的 reactive 邏輯。
6. `types/`
   - TypeScript 型別與資料結構定義。
7. `utils/`
   - 純函式工具與資料轉接 helper。
8. `router/`
   - 路由入口與頁面掛載規則。
9. `styles/`
   - 全域或第三方樣式資產。

## 責任邊界

1. 頁面入口與頁面層資料協調，應放 `views/`
2. 可重用畫面區塊，應放 `components/`
3. 後端呼叫與 request/response 封裝，應放 `services/`
4. 跨頁共享狀態，應放 `stores/`
5. 不依賴畫面的純工具函式，應放 `utils/`

## 維護原則

1. 前端結構應優先維持 view、component、service、store、type 的分層清楚。
2. 若某段邏輯已能獨立命名、重用或測試，應適時從頁面中拆出。
3. 與後端契約直接相關的型別與 mapping，應避免散落在 component 內。
