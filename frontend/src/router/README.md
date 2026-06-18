# Frontend Router 目錄說明

`frontend/src/router/` 負責前端路由註冊與頁面入口配置，是 route path、view 對應與基本守門邏輯的集中位置。

## 責任範圍

本目錄應負責以下內容：

1. route path 與 view 對應
2. 頁面切換層級的導向規則
3. 進頁前需要判斷的基本守門邏輯

以下內容不應放在本目錄：

1. 頁面細部商業邏輯
2. 大型畫面狀態管理
3. 可重用 UI 元件內容

## 相鄰目錄邊界

1. route 對應的頁面實作放 `frontend/src/views/`。
2. 可重用 UI 區塊放 `frontend/src/components/`。
3. 需要呼叫 API 或處理 response shape 時，應透過 `frontend/src/services/` 與 `frontend/src/types/`。

## 維護原則

1. router 應聚焦在頁面入口與導向規則，不承擔頁面內部流程。
2. 若守門邏輯已依賴大量 domain 狀態，應重新檢查與 store 或 service 的邊界。
