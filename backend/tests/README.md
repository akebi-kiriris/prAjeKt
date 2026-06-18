# Backend Tests 目錄說明

`backend/tests/` 存放後端 pytest 測試與共用測試設定，用於驗證 API 契約、service 行為、agent 流程與重構後的既有行為。

## 目錄分工

1. `blueprints/`
   - API route 與 HTTP 行為測試。
2. `services/`
   - 業務流程與 service 契約測試。
3. `chains/`
   - agent、chain 與 graph 流程測試。
4. `models/`
   - model 與資料結構相關測試。
5. `conftest.py`
   - fixture、test app 與共用 setup。

## 責任範圍

本目錄應負責以下內容：

1. 驗證 API 契約
2. 驗證 service 邏輯與錯誤情境
3. 驗證 agent / tool / chain 流程
4. 保護重構後的既有行為

以下內容不應放在本目錄：

1. 正式產品程式碼
2. 臨時 debug script
3. 與測試無關的筆記

## 相鄰目錄邊界

1. 被測試的主線程式碼應留在 `backend/blueprints/`、`backend/services/`、`backend/contracts/`、`backend/repositories/` 或其他正式模組。
2. 測試用 fixture、factory 與共用 app setup 優先放 `conftest.py` 或測試 helper，不反向污染正式程式碼。
3. 臨時資料檢查或修復腳本應放 `backend/scripts/`，不要混入 pytest 測試目錄。

## 維護原則

1. 變更 API、service、contract 或 agent 流程時，應同步檢查本目錄。
2. 測試應優先覆蓋成功路徑、邊界條件與錯誤情境。
3. 若 setup 重複過多，應優先收斂到 `conftest.py`。
