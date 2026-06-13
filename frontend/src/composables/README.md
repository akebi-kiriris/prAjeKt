# Frontend Composables 目錄說明

`frontend/src/composables/` 存放可重用的 Composition API 邏輯，讓多個 component 或 view 可以共享相同的 reactive 行為與互動流程。

## 責任範圍

本目錄應負責以下內容：

1. 可被多個 component 重用的互動邏輯
2. 與 Vue reactivity 高度相關的共用程式
3. 不綁定單一畫面結構的狀態協調 helper

以下內容不應放在本目錄：

1. 純字串、陣列或資料轉換工具函式
2. API 封裝
3. 只服務單一大型元件、離開該元件即失去意義的零碎邏輯

## 相鄰目錄邊界

1. 純函式工具應放 `utils/`。
2. API 對接應放 `services/`。
3. 與單一畫面高度綁定的局部實作可先留在 component 或 view。

## 維護原則

1. composable 應有明確重用價值，而非為抽離而抽離。
2. 若邏輯不依賴 reactivity，通常更適合放到 `utils/`。
