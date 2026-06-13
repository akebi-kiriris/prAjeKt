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

## 維護原則

1. 變更 API、service、contract 或 agent 流程時，應同步檢查本目錄。
2. 測試應優先覆蓋成功路徑、邊界條件與錯誤情境。
3. 若 setup 重複過多，應優先收斂到 `conftest.py`。
