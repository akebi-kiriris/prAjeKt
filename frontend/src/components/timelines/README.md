# Frontend Timeline Components 目錄說明

`frontend/src/components/timelines/` 存放 timeline domain 的主要 UI 元件，包含不同檢視模式、詳情對話框，以及週報、風險分析、知識面板等子區塊。

## 責任範圍

本目錄應負責以下內容：

1. timeline domain 的可重用視覺與互動區塊
2. 容器元件與子面板之間的畫面拆分
3. 屬於 timeline 畫面的局部互動與展示邏輯

## 子元件分工原則

1. 容器元件保留資料整合、狀態協調與事件串接。
2. 子面板元件負責單一區塊的展示與局部互動。
3. 只服務單一 panel 的局部邏輯，可先留在該 panel 內維護。

## 相鄰目錄邊界

1. timeline 頁面入口與跨面板流程協調優先放 `frontend/src/views/` 或主容器元件。
2. API 呼叫與 response mapping 放 `frontend/src/services/`。
3. timeline / task / knowledge 相關型別放 `frontend/src/types/`，不要在元件內重複定義後端契約。

## 維護原則

1. 不應將所有 panel 的 loading、error、empty state 全部塞回單一主容器。
2. 與特定區塊強耦合的 formatter 或 helper，應保持在相近的責任範圍內。
3. 元件拆分應以責任清楚與可維護性為前提，而非單純壓縮檔案長度。
