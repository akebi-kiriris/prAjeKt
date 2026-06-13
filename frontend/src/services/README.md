# Frontend Services 目錄說明

`frontend/src/services/` 負責前端對後端 API 與 socket 的呼叫封裝，讓 view、component 與 store 不需要直接處理底層請求細節。

## 責任範圍

本目錄應負責以下內容：

1. 呼叫後端 API
2. 統一 request / response 基礎處理
3. 必要的前端資料轉接
4. 將同一個 domain 的呼叫集中管理

以下內容不應放在本目錄：

1. Vue component 顯示邏輯
2. 頁面互動流程控制
3. 複雜商業規則判斷
4. 大量畫面專屬格式化細節

## 相鄰目錄邊界

1. `types/` 負責定義資料型別與結構。
2. `utils/` 負責純資料轉換與格式化 helper。
3. `components/` / `views/` 負責畫面呈現與互動。
4. `stores/` 負責跨元件共享狀態。

## 維護原則

1. 一個 service 應盡量對應明確 domain。
2. service 回傳資料 shape 應保持穩定，避免 component 自行猜測 API 結構。
3. 若只屬於畫面顯示的衍生欄位，不應在此層過度轉換。
