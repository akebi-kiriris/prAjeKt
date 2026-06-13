# Frontend Types 目錄說明

`frontend/src/types/` 存放前端共用型別，目的是在 API 回傳、前端狀態與 UI 使用資料之間維持穩定且可追蹤的型別邊界。

## 責任範圍

本目錄應負責以下內容：

1. API model 型別
2. 前端 domain model 型別
3. 共用 payload / response type
4. enum-like union type 與共用資料結構

以下內容不應放在本目錄：

1. API 呼叫邏輯
2. 畫面顯示邏輯
3. 純資料轉換函式
4. 欄位驗證函式本體

## 相鄰目錄邊界

1. `services/` 負責實際取得或送出資料。
2. `utils/` 負責將資料從一種 shape 轉成另一種 shape。
3. `components/` / `views/` 負責使用型別後渲染畫面與處理互動。

## 維護原則

1. 共用型別應盡量集中，避免在 component 內重複手寫。
2. 能貼近後端契約時，欄位名稱與語意應盡量一致。
3. API model 與 UI model 若有不同語意，應清楚分層。
4. 廣泛共用的型別應評估是否由 `index.ts` 統一匯出。
