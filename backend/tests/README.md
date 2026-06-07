# backend/tests

這層放後端 pytest 測試與共用測試設定。

## 目錄分工

- `blueprints/`: API route / HTTP 行為測試
- `services/`: 業務流程與 service 契約測試
- `chains/`: agent / chain / graph 流程測試
- `models/`: model 與資料結構相關測試
- `conftest.py`: fixture、test app、共用 setup

## 這層應該負責什麼

- 驗證 API 契約
- 驗證 service 邏輯與錯誤情境
- 驗證 agent / tool / chain 流程
- 保護重構後的既有行為

## 不應該放什麼

- 真正產品程式碼
- 臨時 debug script 長期留存
- 與測試無關的筆記

## 修改判斷

- 改了 API / service / contract / agent 流程時，應同步補或調整這層
- 這層優先測成功路徑、邊界條件與錯誤情境
- 若某類測試重複 setup 很多，優先考慮收斂到 `conftest.py`
