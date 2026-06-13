# Frontend Utils 目錄說明

`frontend/src/utils/` 存放純函式工具與資料轉接 helper，原則上不依賴 Vue component、Pinia store 或畫面生命週期。

## 責任範圍

本目錄應負責以下內容：

1. 純資料轉換
2. 格式化
3. payload mapping
4. 前端欄位驗證 helper
5. 不依賴畫面生命週期的 domain 輔助函式

以下內容不應放在本目錄：

1. API 請求
2. Pinia state 管理
3. 大量 template 專屬互動流程
4. 依賴 Vue reactivity 的狀態操作

## 相鄰目錄邊界

1. `composables/` 負責與 reactive state 密切相關的重用邏輯。
2. `services/` 負責 API 呼叫與回傳邊界。
3. `types/` 負責型別定義，而非函式行為。

## 維護原則

1. utils 應保持輸入輸出清楚，可在不依賴 Vue 環境下執行。
2. 若 helper 已開始依賴 `ref`、`computed`、`watch` 或生命週期，應評估改放 `composables/`。
3. validator、formatter 與 mapper 應維持明確分工，避免責任混雜。
