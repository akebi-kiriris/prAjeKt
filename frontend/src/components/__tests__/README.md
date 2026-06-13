# Frontend Component Tests 目錄說明

`frontend/src/components/__tests__/` 存放前端 component 測試，重點在於驗證元件互動、畫面結果與使用者可見行為。

## 責任範圍

本目錄應優先驗證以下內容：

1. props 改變後畫面是否正確更新
2. 使用者操作後是否有正確 emit 或互動結果
3. loading / error / empty state 是否正確呈現
4. 關鍵使用者流程是否可穩定通過

以下內容通常不以本目錄為主：

1. API 參數是否組裝正確
2. service mapping 細節
3. 純工具函式的低層分支

## 相鄰目錄邊界

1. `services/` 測試偏重資料與呼叫邊界。
2. `utils/` 測試偏重純函式與轉換邏輯。
3. 本目錄偏重使用者能看到與操作到的結果。

## 維護原則

1. component test 應聚焦行為與畫面，而非過度驗證實作細節。
2. 若測試目標與畫面無關，應優先評估是否改放 service 或 utils 層級測試。
