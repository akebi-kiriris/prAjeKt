# Frontend Stores 目錄說明

`frontend/src/stores/` 存放 Pinia store，負責前端跨頁或跨區塊共享的狀態管理。

## 責任範圍

本目錄應負責以下內容：

1. 跨元件共享狀態
2. 前端狀態快取
3. 明確的前端 state transition

以下內容不應放在本目錄：

1. 太細碎且只在單一元件使用的區域狀態
2. 大量 DOM / UI 細節操作
3. 後端 payload 格式驗證規則

## 相鄰目錄邊界

1. 若狀態需被多個 view 或 component 共同讀寫，適合放本目錄。
2. 若只是單頁局部狀態，應優先留在 view 或 component。
3. API 對接與資料取得，應留在 `services/`。

## 維護原則

1. store 應以共享狀態與狀態轉移為中心，不混入畫面細節。
2. 若某段狀態不具共享價值，應避免過早提升到 store 層。
